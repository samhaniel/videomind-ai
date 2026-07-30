import os
import sys
from flask import Flask, send_from_directory, render_template_string, jsonify
from dotenv import load_dotenv

# Safe import for flask_cors
try:
    from flask_cors import CORS
    HAS_CORS = True
except ImportError:
    HAS_CORS = False

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
static_dir = frontend_folder if os.path.exists(os.path.join(frontend_folder, 'index.html')) else root_dir

app = Flask(__name__, static_folder=static_dir, static_url_path='')
app.secret_key = os.getenv("SECRET_KEY", "videomind-secret-key-2026")

if HAS_CORS:
    CORS(app)
else:
    @app.after_request
    def after_request_cors(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

from routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Routes for serving frontend HTML pages
@app.route('/')
def index_page():
    return send_from_directory(frontend_folder, 'index.html')

@app.route('/chat.html')
@app.route('/chat')
def chat_page():
    return send_from_directory(frontend_folder, 'chat.html')

@app.route('/history.html')
@app.route('/history')
def history_page():
    return send_from_directory(frontend_folder, 'history.html')

@app.route('/settings.html')
@app.route('/settings')
def settings_page():
    return send_from_directory(frontend_folder, 'settings.html')

# Catch-all route for static assets (CSS, JS, images)
@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    if path.startswith('api/') or path.startswith('api'):
        return jsonify({"error": "API endpoint not found", "success": False}), 404
    if os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    return send_from_directory(static_dir, 'index.html')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    use_reloader = os.getenv("USE_RELOADER", "False").lower() == "true"
    print(f"🚀 Summarize Chatbot Server starting on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=use_reloader)

