import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app import app

class VercelWSGIHandler:
    """
    WSGI middleware for Vercel Python serverless execution.
    Fixes PATH_INFO for POST /api/analyze, POST /api/summary, POST /api/chat, etc.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get('HTTP_X_MATCHED_PATH', '') or 
            environ.get('REQUEST_URI', '') or 
            environ.get('HTTP_X_ORIGINAL_URI', '') or 
            environ.get('PATH_INFO', '')
        )
        if matched_path:
            clean_path = matched_path.split('?')[0]
            if clean_path and clean_path not in ['/api/index.py', '/api/index']:
                environ['PATH_INFO'] = clean_path
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIHandler(app.wsgi_app)
