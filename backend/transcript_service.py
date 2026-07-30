import os
import logging
from typing import Dict, Any, List
from utils import format_timestamp, chunk_transcript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_proxy_config():
    """
    Build a proxy configuration for youtube-transcript-api if credentials are provided.

    IMPORTANT: YouTube blocks most requests coming from cloud-provider IP ranges
    (AWS, GCP, Azure, and by extension Vercel's serverless infrastructure). This means
    transcript fetches that work fine on localhost will fail on Vercel with
    RequestBlocked / IpBlocked errors unless routed through a proxy.

    Configure one of the following in your environment (Vercel Project Settings -> Environment Variables):
      - WEBSHARE_PROXY_USERNAME / WEBSHARE_PROXY_PASSWORD (recommended: youtube-transcript-api's
        built-in rotating-residential-proxy integration via Webshare)
      - GENERIC_PROXY_URL (a single http(s) proxy URL usable for both http and https traffic)
    """
    webshare_user = os.getenv("WEBSHARE_PROXY_USERNAME", "").strip()
    webshare_pass = os.getenv("WEBSHARE_PROXY_PASSWORD", "").strip()
    if webshare_user and webshare_pass:
        try:
            from youtube_transcript_api.proxies import WebshareProxyConfig
            return WebshareProxyConfig(
                proxy_username=webshare_user,
                proxy_password=webshare_pass,
            )
        except Exception as e:
            logger.warning(f"Could not build WebshareProxyConfig: {str(e)}")

    generic_proxy_url = os.getenv("GENERIC_PROXY_URL", "").strip()
    if generic_proxy_url:
        try:
            from youtube_transcript_api.proxies import GenericProxyConfig
            return GenericProxyConfig(
                http_url=generic_proxy_url,
                https_url=generic_proxy_url,
            )
        except Exception as e:
            logger.warning(f"Could not build GenericProxyConfig: {str(e)}")

    return None


class TranscriptService:
    @staticmethod
    def fetch_transcript(video_id: str, languages: List[str] = None) -> Dict[str, Any]:
        """
        Fetch closed captions / transcript entries for a video ID.
        Robustly supports manual, auto-generated, and multi-language transcripts across API versions.
        """
        if languages is None:
            languages = ['en', 'en-US', 'en-GB', 'ta', 'hi', 'es', 'fr', 'de', 'pt', 'ja', 'ko']
            
        raw_items = []
        has_transcript = False
        error_message = None
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api_transcript = None
            proxy_config = _build_proxy_config()
            
            # Strategy 1: Use instance list() which supports auto-generated & multi-language captions
            try:
                yt = YouTubeTranscriptApi(proxy_config=proxy_config) if proxy_config else YouTubeTranscriptApi()
                if hasattr(yt, 'list'):
                    t_list = yt.list(video_id)
                    # Try manually created transcript first
                    try:
                        t = t_list.find_manually_created_transcript(languages)
                        api_transcript = t.fetch()
                    except Exception:
                        pass
                    
                    # Try auto-generated transcript second
                    if not api_transcript:
                        try:
                            t = t_list.find_generated_transcript(languages)
                            api_transcript = t.fetch()
                        except Exception:
                            pass
                            
                    # Fallback to any transcript available in list
                    if not api_transcript:
                        for t in t_list:
                            try:
                                api_transcript = t.fetch()
                                if api_transcript:
                                    break
                            except Exception:
                                continue
            except Exception as e1:
                logger.debug(f"Strategy 1 (list) failed for {video_id}: {str(e1)}")
                if "block" in str(e1).lower():
                    error_message = str(e1)

            # Strategy 2: Direct fetch / get_transcript (legacy static API, no proxy support)
            if not api_transcript and not proxy_config:
                try:
                    if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                        api_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                except Exception as e2:
                    logger.debug(f"Strategy 2 (get_transcript with languages) failed: {str(e2)}")
                    if "block" in str(e2).lower():
                        error_message = str(e2)

            # Strategy 3: Unconstrained get_transcript (legacy static API, no proxy support)
            if not api_transcript and not proxy_config:
                try:
                    if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                        api_transcript = YouTubeTranscriptApi.get_transcript(video_id)
                except Exception as e3:
                    logger.debug(f"Strategy 3 (get_transcript default) failed: {str(e3)}")
                    if "block" in str(e3).lower():
                        error_message = str(e3)

            if api_transcript:
                has_transcript = True
                for entry in api_transcript:
                    if isinstance(entry, dict):
                        text = entry.get("text", "").replace("\n", " ").strip()
                        start = float(entry.get("start", 0))
                        duration = float(entry.get("duration", 0))
                    else:
                        text = getattr(entry, "text", "").replace("\n", " ").strip()
                        start = float(getattr(entry, "start", 0))
                        duration = float(getattr(entry, "duration", 0))
                        
                    if text:
                        raw_items.append({
                            "text": text,
                            "start": start,
                            "duration": duration,
                            "timestamp": format_timestamp(start)
                        })
        except Exception as e:
            logger.error(f"Could not retrieve transcript for {video_id}: {str(e)}")
            if "block" in str(e).lower():
                error_message = str(e)

        if not has_transcript or not raw_items:
            if error_message and "block" in error_message.lower():
                msg = ("⚠️ YouTube is blocking transcript requests from this server's IP address "
                       "(this is common on cloud hosts like Vercel). Configure a residential proxy "
                       "(WEBSHARE_PROXY_USERNAME / WEBSHARE_PROXY_PASSWORD, or GENERIC_PROXY_URL) "
                       "in your environment variables to fix this.")
            else:
                msg = ("⚠️ Closed captions / transcript are currently disabled or unavailable for this "
                       "YouTube video. Summarize Chatbot relies on transcript analysis to guarantee "
                       "accurate, non-hallucinated insights. Please try a video with closed captions enabled.")
            return {
                "has_transcript": False,
                "error_message": msg,
                "items": [],
                "full_text": "",
                "chunks": [],
                "total_duration": 0,
                "word_count": 0
            }

        full_text = "\n".join([f"[{item['timestamp']}] {item['text']}" for item in raw_items])
        chunks = chunk_transcript(raw_items, chunk_size=1500, overlap=200)
        total_duration = raw_items[-1]["start"] + raw_items[-1]["duration"] if raw_items else 0
        word_count = sum(len(item["text"].split()) for item in raw_items)

        return {
            "has_transcript": True,
            "error_message": "",
            "items": raw_items,
            "full_text": full_text,
            "chunks": chunks,
            "total_duration": total_duration,
            "duration_formatted": format_timestamp(total_duration),
            "word_count": word_count
        }

transcript_service = TranscriptService()
