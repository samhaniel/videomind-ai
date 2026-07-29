import logging
from typing import Dict, Any, List
from utils import format_timestamp, chunk_transcript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptService:
    @staticmethod
    def fetch_transcript(video_id: str, languages: List[str] = None) -> Dict[str, Any]:
        """
        Fetch closed captions / transcript entries for a video ID.
        Supports youtube-transcript-api v1.2.4+ (fetch/list) and legacy v0.6+ (get_transcript).
        """
        if languages is None:
            languages = ['en', 'en-US', 'en-GB', 'es', 'fr', 'de', 'hi', 'pt', 'ja', 'ko']
            
        raw_items = []
        has_transcript = False
        
        try:
            import youtube_transcript_api
            from youtube_transcript_api import YouTubeTranscriptApi
            
            api_transcript = None
            
            # 1. Try modern v1.2+ API: YouTubeTranscriptApi().fetch(video_id) or YouTubeTranscriptApi.fetch(video_id)
            try:
                if hasattr(YouTubeTranscriptApi, 'fetch'):
                    try:
                        api_transcript = YouTubeTranscriptApi.fetch(video_id, languages=languages)
                    except TypeError:
                        api_transcript = YouTubeTranscriptApi.fetch(video_id)
                elif hasattr(YouTubeTranscriptApi, 'get_transcript'):
                    api_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            except Exception as e1:
                logger.debug(f"Direct transcript fetch failed: {str(e1)}")
                
            # 2. Try instance fallback
            if not api_transcript:
                try:
                    yt = YouTubeTranscriptApi()
                    if hasattr(yt, 'fetch'):
                        try:
                            api_transcript = yt.fetch(video_id, languages=languages)
                        except TypeError:
                            api_transcript = yt.fetch(video_id)
                    elif hasattr(yt, 'get_transcript'):
                        api_transcript = yt.get_transcript(video_id, languages=languages)
                except Exception as e2:
                    logger.debug(f"Instance fetch failed: {str(e2)}")

            # 3. Try transcript list fallback
            if not api_transcript:
                try:
                    t_list = None
                    if hasattr(YouTubeTranscriptApi, 'list'):
                        t_list = YouTubeTranscriptApi.list(video_id)
                    elif hasattr(YouTubeTranscriptApi, 'list_transcripts'):
                        t_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    elif hasattr(YouTubeTranscriptApi(), 'list'):
                        t_list = YouTubeTranscriptApi().list(video_id)
                        
                    if t_list:
                        for t in t_list:
                            api_transcript = t.fetch()
                            break
                except Exception as e3:
                    logger.warning(f"List transcript fallback error for {video_id}: {str(e3)}")

            if api_transcript:
                has_transcript = True
                for entry in api_transcript:
                    # Handle both dictionary entries and FetchedTranscriptSnippet objects
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

        if not has_transcript or not raw_items:
            return {
                "has_transcript": False,
                "error_message": "⚠️ Closed captions / transcript are currently disabled or unavailable for this YouTube video. Summarize Chatbot relies on transcript analysis to guarantee accurate, non-hallucinated insights. Please try a video with closed captions enabled.",
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
