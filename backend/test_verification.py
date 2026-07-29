import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import extract_youtube_id, format_timestamp, chunk_transcript
from transcript import process_video_url
from summary import generate_ai_summary
from chat import answer_video_question, generate_learning_asset

def run_tests():
    print("--- 🧪 VideoMind AI Automated Backend Verification ---")
    
    # 1. URL Extraction Test
    sample_url = "https://www.youtube.com/watch?v=aircAruvnKk"
    vid_id = extract_youtube_id(sample_url)
    assert vid_id == "aircAruvnKk", f"Expected aircAruvnKk, got {vid_id}"
    print("✅ Video ID extraction verified:", vid_id)
    
    # 2. Timestamp Formatting Test
    formatted_ts = format_timestamp(125.5)
    assert formatted_ts == "02:05", f"Expected 02:05, got {formatted_ts}"
    print("✅ Timestamp formatting verified:", formatted_ts)
    
    # 3. Pipeline Test
    result = process_video_url(sample_url)
    assert result["success"] == True
    print("✅ Video processing pipeline verified:", result["metadata"]["title"])
    
    # 4. Summary Test
    summary = generate_ai_summary(vid_id, result["metadata"]["title"], result["full_text"], style="quick")
    assert summary["success"] == True
    print("✅ Summary engine verified:", summary["summary_style"])
    
    # 5. Grounded Q&A Test
    qa = answer_video_question(result["metadata"]["title"], result["transcript"], "What is the main topic?")
    assert qa["success"] == True
    print("✅ Grounded Q&A engine verified:", qa["source"])
    
    # 6. Flashcard Generation Test
    fc = generate_learning_asset(result["metadata"]["title"], result["full_text"], "flashcards")
    assert fc["success"] == True
    print("✅ Flashcard generator verified:", fc["source"])
    
    print("\n🎉 ALL BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
