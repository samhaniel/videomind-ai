import os
import json
import logging
import tempfile
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Vercel (and most serverless platforms) only allow writes to /tmp - the rest of the
# deployed project filesystem is read-only. tempfile.gettempdir() resolves to /tmp
# automatically in that environment and to the OS temp dir locally, so this works
# in both places without any extra configuration.
IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

# Firebase Firestore helper wrapper
class FirebaseService:
    def __init__(self):
        self.initialized = False
        self.db = None
        self._init_firebase()
        
    def _init_firebase(self):
        # Service account or credentials config check
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
        if cred_path and os.path.exists(cred_path):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                
                if not firebase_admin._apps:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.initialized = True
                logger.info("Firebase Admin initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Firebase Admin: {str(e)}")
        else:
            logger.info("Firebase Admin running in client-side / local storage sync mode.")
            
    def save_analyzed_video(self, user_id: str, video_data: Dict[str, Any]) -> bool:
        if not self.initialized or not self.db:
            return False
        try:
            doc_ref = self.db.collection("users").document(user_id).collection("videos").document(video_data["video_id"])
            doc_ref.set(video_data, merge=True)
            return True
        except Exception as e:
            logger.error(f"Error saving video to Firebase: {str(e)}")
            return False

    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.initialized or not self.db:
            return []
        try:
            docs = self.db.collection("users").document(user_id).collection("videos").order_by("timestamp", direction="DESCENDING").limit(50).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error retrieving history from Firebase: {str(e)}")
            return []

    def delete_user_history_item(self, user_id: str, video_id: str) -> bool:
        if not self.initialized or not self.db:
            return False
        try:
            self.db.collection("users").document(user_id).collection("videos").document(video_id).delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting video from Firebase: {str(e)}")
            return False

    def _get_cache_filepath(self) -> str:
        if IS_SERVERLESS:
            cache_dir = os.path.join(tempfile.gettempdir(), "videomind_cache")
        else:
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, "session_cache.json")

    def save_session_cache(self, video_id: str, session_data: Dict[str, Any]) -> None:
        """Persist session data (transcript chunks & metadata) to local disk cache."""
        try:
            cache_file = self._get_cache_filepath()
            cache = {}
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            cache[video_id] = session_data
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write session cache to disk: {str(e)}")

    def get_session_cache(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from local disk cache."""
        try:
            cache_file = self._get_cache_filepath()
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    return cache.get(video_id)
        except Exception as e:
            logger.warning(f"Failed to read session cache from disk: {str(e)}")
        return None

firebase_service = FirebaseService()

