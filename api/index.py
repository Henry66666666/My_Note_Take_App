import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'src', 'static')

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

# 配置数据库 - 优先使用 Supabase
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # 使用 Supabase PostgreSQL
    # 修复 postgres:// 到 postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print("✅ Using Supabase PostgreSQL database")
else:
    # 回退到内存数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    print("⚠️ Using in-memory SQLite database (data will not persist)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义 Note 模型
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Import routes after app is configured
try:
    from src.routes.user import user_bp
    from src.routes.note import note_bp
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(note_bp, url_prefix='/api')
    print("✅ Routes registered successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not import routes: {e}")

# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created")

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
        "database": "Supabase PostgreSQL" if DATABASE_URL else "In-memory SQLite",
        "endpoints": {
            "notes": "/api/notes",
            "users": "/api/users"
        }
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
        "database": "Supabase PostgreSQL" if DATABASE_URL else "In-memory SQLite",
        "static_dir": STATIC_DIR,
        "static_exists": os.path.exists(STATIC_DIR),
        "index_exists": os.path.exists(os.path.join(STATIC_DIR, 'index.html'))
    })

# This is required for Vercel
app = app
