import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any
from utils import extract_youtube_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeService:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if provided string is a valid YouTube URL or Video ID."""
        video_id = extract_youtube_id(url)
        return bool(video_id and len(video_id) == 11)

    @staticmethod
    def get_video_id(url: str) -> str:
        """Extract 11-character video ID."""
        return extract_youtube_id(url)

    @staticmethod
    def fetch_metadata(video_id: str) -> Dict[str, Any]:
        """Retrieve video metadata via YouTube oEmbed endpoint."""
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
            logger.warning(f"Metadata oEmbed fetch warning for {video_id}: {str(e)}")
            
        return metadata

youtube_service = YouTubeService()
