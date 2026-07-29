import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, List
from utils import extract_youtube_id, format_timestamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_video_metadata(video_id: str) -> Dict[str, Any]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
    
    metadata = {
        "video_id": video_id,
        "url": url,
        "title": f"YouTube Video ({video_id})",
        "author": "YouTube Creator",
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "embed_url": f"https://www.youtube.com/embed/{video_id}"
    }
    
    try:
        req = urllib.request.Request(
            oembed_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                metadata["title"] = data.get("title", metadata["title"])
                metadata["author"] = data.get("author_name", metadata["author"])
                if data.get("thumbnail_url"):
                    metadata["thumbnail_url"] = data.get("thumbnail_url")
    except Exception as e:
        logger.warning(f"Could not fetch oEmbed metadata for {video_id}: {str(e)}")
        
    return metadata

def get_youtube_transcript(video_id: str, languages: List[str] = None) -> List[Dict[str, Any]]:
    if languages is None:
        languages = ['en', 'en-US', 'en-GB', 'es', 'fr', 'de', 'hi', 'pt']
        
    transcript_items = []
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api_transcript = None
        
        try:
            if hasattr(YouTubeTranscriptApi, 'fetch'):
                try:
                    api_transcript = YouTubeTranscriptApi.fetch(video_id, languages=languages)
                except TypeError:
                    api_transcript = YouTubeTranscriptApi.fetch(video_id)
            elif hasattr(YouTubeTranscriptApi, 'get_transcript'):
                api_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except Exception:
            try:
                yt = YouTubeTranscriptApi()
                if hasattr(yt, 'fetch'):
                    try:
                        api_transcript = yt.fetch(video_id, languages=languages)
                    except TypeError:
                        api_transcript = yt.fetch(video_id)
            except Exception:
                pass
                
        if api_transcript:
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
                    transcript_items.append({
                        "text": text,
                        "start": start,
                        "duration": duration,
                        "timestamp": format_timestamp(start)
                    })
    except Exception as e:
        logger.warning(f"Transcript extraction error for {video_id}: {str(e)}")
        
    return transcript_items

def generate_fallback_transcript(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    title = metadata.get("title", "Video Analysis")
    author = metadata.get("author", "Creator")
    return [{
        "text": f"This is an automated context synthesis for video '{title}' by {author}.",
        "start": 0.0,
        "duration": 60.0,
        "timestamp": "00:00"
    }]

def process_video_url(url: str) -> Dict[str, Any]:
    video_id = extract_youtube_id(url)
    if not video_id:
        return {"success": False, "error": "Invalid YouTube URL format."}
        
    metadata = fetch_video_metadata(video_id)
    transcript_items = get_youtube_transcript(video_id)
    has_captions = True
    
    if not transcript_items:
        has_captions = False
        transcript_items = generate_fallback_transcript(metadata)
        
    full_text = "\n".join([f"[{item['timestamp']}] {item['text']}" for item in transcript_items])
    total_duration = transcript_items[-1]["start"] + transcript_items[-1]["duration"] if transcript_items else 0
    
    return {
        "success": True,
        "video_id": video_id,
        "metadata": metadata,
        "has_captions": has_captions,
        "transcript": transcript_items,
        "full_text": full_text,
        "duration_seconds": total_duration,
        "duration_formatted": format_timestamp(total_duration),
        "word_count": sum(len(item["text"].split()) for item in transcript_items)
    }
