import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
from src.models.user import db

# Get project directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'src', 'static')

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS
CORS(app)

# Use in-memory database for Vercel (serverless doesn't persist files)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Import routes after app is configured
from src.routes.user import user_bp
from src.routes.note import note_bp

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')

# Create tables
with app.app_context():
    db.create_all()

# Serve the main HTML page
@app.route('/')
def home():
    try:
        index_path = os.path.join(STATIC_DIR, 'index.html')
        if os.path.exists(index_path):
            return send_file(index_path)
    except Exception as e:
        print(f"Error serving index.html: {e}")
    
    return jsonify({
        "message": "Note Taking API is running on Vercel",
        "status": "ok",
        "endpoints": {
            "notes": "/api/notes",
            "users": "/api/users"
        },
        "error": "index.html not found"
    })

# Serve static files (CSS, JS, images, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
    try:
        # Check if file exists in static directory
        file_path = os.path.join(STATIC_DIR, filename)
        if os.path.exists(file_path):
            return send_from_directory(STATIC_DIR, filename)
    except Exception as e:
        print(f"Error serving {filename}: {e}")
    
    # If not a static file, return 404
    return jsonify({"error": "File not found"}), 404

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "database": "in-memory",
        "static_dir": STATIC_DIR,
        "static_exists": os.path.exists(STATIC_DIR),
        "index_exists": os.path.exists(os.path.join(STATIC_DIR, 'index.html'))
    })

# This is required for Vercel
app = app
