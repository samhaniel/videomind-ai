import time
import logging
from flask import Blueprint, request, jsonify
from youtube_service import youtube_service
from transcript_service import transcript_service
from chat_service import chat_service
from firebase_service import firebase_service
from chat import generate_learning_asset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# In-memory session cache backed by disk cache
VIDEO_CACHE = {}

def success_response(data=None, message="Success"):
    return jsonify({
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }), 200

def error_response(error="An error occurred", status_code=400):
    return jsonify({
        "success": False,
        "error": str(error)
    }), status_code

def get_or_load_session(video_id: str, url: str = None):
    """Retrieve session data from memory cache, disk cache, or live fetch."""
    if not video_id:
        return None
        
    if video_id in VIDEO_CACHE:
        return VIDEO_CACHE[video_id]
        
    # Check disk cache
    cached = firebase_service.get_session_cache(video_id)
    if cached:
        VIDEO_CACHE[video_id] = cached
        return cached
        
    # Re-fetch transcript if missing
    target_url = url or f"https://www.youtube.com/watch?v={video_id}"
    v_id = youtube_service.get_video_id(target_url) or video_id
    metadata = youtube_service.fetch_metadata(v_id)
    transcript_res = transcript_service.fetch_transcript(v_id)
    
    if transcript_res.get("has_transcript"):
        session_data = {
            "video_id": v_id,
            "metadata": metadata,
            "transcript": transcript_res["items"],
            "chunks": transcript_res["chunks"],
            "full_text": transcript_res["full_text"],
            "duration_formatted": transcript_res["duration_formatted"],
            "word_count": transcript_res["word_count"]
        }
        VIDEO_CACHE[v_id] = session_data
        firebase_service.save_session_cache(v_id, session_data)
        return session_data
        
    return None

@api_bp.route('/health', methods=['GET'])
def health_check():
    return success_response({
        "status": "online",
        "app": "Summarize Chatbot AI",
        "version": "2.0.0",
        "timestamp": time.time()
    }, "System operational")

@api_bp.route('/analyze', methods=['POST'])
def analyze_video():
    try:
        data = request.get_json() or {}
        url = data.get("url", "").strip()
        
        if not url:
            return error_response("Please paste a valid YouTube URL.", 400)
            
        if not youtube_service.validate_url(url):
            return error_response("Invalid YouTube URL format. Please provide a valid YouTube link.", 400)
            
        video_id = youtube_service.get_video_id(url)
        metadata = youtube_service.fetch_metadata(video_id)
        transcript_res = transcript_service.fetch_transcript(video_id)
        
        if not transcript_res.get("has_transcript"):
            return jsonify({
                "success": False,
                "error": transcript_res.get("error_message", "No transcript available for this video."),
                "data": {
                    "video_id": video_id,
                    "metadata": metadata,
                    "has_transcript": False
                }
            }), 400
            
        session_data = {
            "video_id": video_id,
            "metadata": metadata,
            "transcript": transcript_res["items"],
            "chunks": transcript_res["chunks"],
            "full_text": transcript_res["full_text"],
            "duration_formatted": transcript_res["duration_formatted"],
            "word_count": transcript_res["word_count"]
        }
        
        VIDEO_CACHE[video_id] = session_data
        firebase_service.save_session_cache(video_id, session_data)
        
        user_id = data.get("user_id", "anonymous")
        firebase_service.save_analyzed_video(user_id, {
            "video_id": video_id,
            "title": metadata["title"],
            "author": metadata["author"],
            "thumbnail_url": metadata["thumbnail_url"],
            "url": metadata["url"],
            "duration": transcript_res["duration_formatted"],
            "timestamp": time.time()
        })
        
        return success_response({
            "video_id": video_id,
            "metadata": metadata,
            "has_transcript": True,
            "duration": transcript_res["duration_formatted"],
            "word_count": transcript_res["word_count"],
            "transcript_preview": transcript_res["items"][:5]
        }, "Video analysis completed successfully")
    except Exception as e:
        logger.error(f"Unhandled error in /analyze: {str(e)}", exc_info=True)
        return error_response(f"Server error analyzing video: {str(e)}", 500)

@api_bp.route('/summary', methods=['POST'])
def get_summary():
    try:
        data = request.get_json() or {}
        video_id = data.get("video_id", "").strip()
        style = data.get("style", "quick").strip()
        url = data.get("url", "").strip()
        
        if not video_id:
            return error_response("Video ID is required.", 400)
            
        session_data = get_or_load_session(video_id, url)
        if not session_data:
            return error_response("No transcript available for this video.", 404)
            
        title = session_data["metadata"]["title"]
        full_text = session_data["full_text"]
        
        result = chat_service.generate_analysis(title, full_text, style=style)
        return success_response(result, "Summary generated successfully")
    except Exception as e:
        logger.error(f"Error in /summary: {str(e)}", exc_info=True)
        return error_response(f"Failed to generate summary: {str(e)}", 500)

@api_bp.route('/chat', methods=['POST'])
def chat_with_video():
    try:
        data = request.get_json() or {}
        video_id = data.get("video_id", "").strip()
        question = data.get("question", "").strip()
        url = data.get("url", "").strip()
        
        if not video_id or not question:
            return error_response("Video ID and question are required.", 400)
            
        session_data = get_or_load_session(video_id, url)
        if not session_data or not session_data.get("chunks"):
            return error_response("No transcript available for this video.", 404)
            
        title = session_data["metadata"]["title"]
        chunks = session_data["chunks"]
        
        result = chat_service.answer_question(title, chunks, question)
        return success_response(result, "Question answered successfully")
    except Exception as e:
        logger.error(f"Error in /chat: {str(e)}", exc_info=True)
        return error_response(f"Failed to process chat: {str(e)}", 500)

@api_bp.route('/generate', methods=['POST'])
def generate_asset_route():
    try:
        data = request.get_json() or {}
        video_id = data.get("video_id", "").strip()
        asset_type = data.get("asset_type", "flashcards").strip()
        url = data.get("url", "").strip()
        
        if not video_id:
            return error_response("Video ID is required.", 400)
            
        session_data = get_or_load_session(video_id, url)
        if not session_data:
            return error_response("No transcript available for this video.", 404)
            
        title = session_data["metadata"]["title"]
        full_text = session_data["full_text"]
        
        result = generate_learning_asset(title, full_text, asset_type)
        return success_response(result, f"Asset '{asset_type}' generated successfully")
    except Exception as e:
        logger.error(f"Error in /generate: {str(e)}", exc_info=True)
        return error_response(f"Failed to generate asset: {str(e)}", 500)

@api_bp.route('/history', methods=['GET'])
def get_history():
    try:
        user_id = request.args.get("user_id", "anonymous")
        history_items = firebase_service.get_user_history(user_id)
        if not history_items:
            history_items = [
                {
                    "video_id": vid,
                    "title": data["metadata"]["title"],
                    "author": data["metadata"]["author"],
                    "thumbnail_url": data["metadata"]["thumbnail_url"],
                    "url": data["metadata"]["url"],
                    "duration": data["duration_formatted"],
                    "timestamp": time.time()
                }
                for vid, data in VIDEO_CACHE.items()
            ]
        return success_response({"history": history_items}, "History retrieved")
    except Exception as e:
        logger.error(f"Error in /history: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch history: {str(e)}", 500)
