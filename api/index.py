import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, send_from_directory, send_file, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# 🔍 Vercel 环境变量检查 (调试用)
print("=" * 60)
print("🔍 Vercel 环境变量检查:")
DATABASE_URL = os.environ.get('DATABASE_URL')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
print(f"DATABASE_URL 存在: {DATABASE_URL is not None}")
print(f"GITHUB_TOKEN 存在: {GITHUB_TOKEN is not None}")
if DATABASE_URL:
    # 仅显示前20个字符以保护隐私
    print(f"DATABASE_URL 前缀: {DATABASE_URL[:20]}...")
print("=" * 60)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'src', 'static')

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

# 配置数据库 - 优先使用 Supabase
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

# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created")

# ====================== API Routes ======================

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    try:
        notes = Note.query.order_by(Note.updated_at.desc()).all()
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        print(f"Error getting notes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        note = Note(
            title=data['title'],
            content=data['content'],
            tags=','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', '')
        )
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating note: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    try:
        note = Note.query.get_or_404(note_id)
        return jsonify(note.to_dict())
    except Exception as e:
        print(f"Error getting note {note_id}: {e}")
        return jsonify({'error': str(e)}), 404

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        if 'tags' in data:
            note.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data.get('tags', '')
        
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        print(f"Error updating note {note_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting note {note_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify([])
        
        notes = Note.query.filter(
            db.or_(
                Note.title.ilike(f'%{query}%'),
                Note.content.ilike(f'%{query}%')
            )
        ).order_by(Note.updated_at.desc()).all()
        
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        print(f"Error searching notes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/generate', methods=['POST'])
def generate_note():
    """Generate a note using AI"""
    try:
        data = request.json
        # 支持两种参数格式: prompt 或 text
        prompt = data.get('prompt') or data.get('text')
        
        if not prompt:
            return jsonify({'error': 'Prompt or text is required'}), 400
        
        # Import LLM functions
        try:
            from src.llm import extract_structured_notes
            result = extract_structured_notes(prompt)
            
            # 确保返回格式包含前端期望的字段
            if isinstance(result, str):
                # 如果返回的是字符串,尝试解析为 JSON
                import json
                try:
                    result = json.loads(result)
                except:
                    # 如果解析失败,创建一个标准格式
                    result = {
                        'title': 'Generated Note',
                        'content': result,
                        'tags': []
                    }
            
            # 创建新笔记并保存到数据库
            note = Note(
                title=result.get('title', result.get('Title', 'Generated Note')),
                content=result.get('content', result.get('notes', result.get('Notes', ''))),
                tags=','.join(result.get('tags', result.get('Tags', []))) if isinstance(result.get('tags', result.get('Tags', [])), list) else ''
            )
            db.session.add(note)
            db.session.commit()
            
            return jsonify(note.to_dict()), 200
            
        except ImportError:
            return jsonify({'error': 'AI feature not available'}), 503
        except Exception as llm_error:
            print(f"LLM error: {llm_error}")
            return jsonify({'error': f'AI generation failed: {str(llm_error)}'}), 500
            
    except Exception as e:
        print(f"Error generating note: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<int:note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate a note to another language"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data or 'target_language' not in data:
            return jsonify({'error': 'Target language is required'}), 400
        
        # Import LLM functions
        try:
            from src.llm import translate
            translated_content = translate(note.content, data['target_language'])
            return jsonify({
                'original_content': note.content,
                'translated_content': translated_content,
                'target_language': data['target_language']
            })
        except ImportError:
            return jsonify({'error': 'Translation feature not available'}), 503
        except Exception as llm_error:
            print(f"Translation error: {llm_error}")
            return jsonify({'error': f'Translation failed: {str(llm_error)}'}), 500
            
    except Exception as e:
        print(f"Error translating note: {e}")
        return jsonify({'error': str(e)}), 500

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
    """健康检查端点 - 返回详细的系统状态"""
    db_status = "disconnected"
    db_error = None
    
    try:
        # 尝试执行简单的数据库查询
        db.session.execute(text('SELECT 1'))
        db_status = "connected"
    except Exception as e:
        db_error = str(e)
    
    return jsonify({
        "status": "healthy",
        "database": "Supabase PostgreSQL" if DATABASE_URL else "In-memory SQLite",
        "database_url_exists": DATABASE_URL is not None,
        "database_status": db_status,
        "database_error": db_error,
        "github_token_exists": os.environ.get('GITHUB_TOKEN') is not None,
        "static_dir": STATIC_DIR,
        "static_exists": os.path.exists(STATIC_DIR),
        "index_exists": os.path.exists(os.path.join(STATIC_DIR, 'index.html'))
    })

# This is required for Vercel
app = app
