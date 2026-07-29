import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from youtube_service import youtube_service
from transcript_service import transcript_service
from chat_service import chat_service

def debug_video(url):
    print(f"\n--- Testing Video: {url} ---")
    try:
        video_id = youtube_service.get_video_id(url)
        print(f"Video ID: {video_id}")
        
        metadata = youtube_service.fetch_metadata(video_id)
        print(f"Title: {metadata['title']}")
        
        transcript_res = transcript_service.fetch_transcript(video_id)
        print(f"Has Transcript: {transcript_res['has_transcript']}")
        if not transcript_res['has_transcript']:
            print(f"Transcript Error: {transcript_res['error_message']}")
            return
            
        print(f"Word Count: {transcript_res['word_count']}")
        print(f"Chunks Count: {len(transcript_res['chunks'])}")
        
        # Test Gemini Summary
        print("Calling Gemini API for Quick Summary...")
        summary = chat_service.generate_analysis(metadata['title'], transcript_res['full_text'], style='quick')
        print(f"Summary Success: {summary['success']}, Source: {summary.get('source')}")
        print("Summary Preview:\n", summary.get('content')[:300])
        
    except Exception as e:
        print("❌ EXCEPTION OCCURRED:")
        traceback.print_exc()

if __name__ == "__main__":
    test_urls = [
        "https://www.youtube.com/watch?v=aircAruvnKk", # 3Blue1Brown
        "https://www.youtube.com/watch?v=kqtD5dpn9C8", # FreeCodeCamp
        "https://youtu.be/dQw4w9WgXcQ"                  # Rick Astley
    ]
    for url in test_urls:
        debug_video(url)
