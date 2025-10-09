import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS
from src.models.user import db

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

@app.route('/')
def home():
    return jsonify({
        "message": "Note Taking API is running on Vercel",
        "status": "ok",
        "endpoints": {
            "notes": "/api/notes",
            "users": "/api/users"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# This is required for Vercel
app = app
