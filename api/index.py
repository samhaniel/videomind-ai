import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app import app

class VercelMiddleware:
    """
    WSGI Middleware for Vercel Serverless Functions.
    Restores the original PATH_INFO from request headers so Flask routes (/api/analyze, /api/chat, etc.) work accurately.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Vercel passes the original URL path in HTTP_X_MATCHED_PATH or REQUEST_URI
        matched_path = environ.get('HTTP_X_MATCHED_PATH', '') or environ.get('REQUEST_URI', '')
        if matched_path:
            clean_path = matched_path.split('?')[0]
            if clean_path:
                environ['PATH_INFO'] = clean_path
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelMiddleware(app.wsgi_app)
