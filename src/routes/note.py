from flask import Blueprint, jsonify, request
from src.models.note import Note, db
from src.llm import translate, extract_structured_notes
import json

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        note = Note(title=data['title'], content=data['content'])
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes/<int:note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate a note's title and content"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data or 'target_language' not in data:
            return jsonify({'error': 'Target language is required'}), 400
        
        target_language = data['target_language']
        
        # Translate title and content
        translated_title = translate(note.title, target_language) if note.title else ""
        translated_content = translate(note.content, target_language) if note.content else ""
        
        # Update the note with translated content
        note.title = translated_title
        note.content = translated_content
        db.session.commit()
        
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/generate', methods=['POST'])
def generate_note():
    """Generate a structured note from user input text"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'Text input is required'}), 400
        
        input_text = data['text']
        language = data.get('language', 'English')
        
        # Use extract_structured_notes to generate structured note
        extracted_result = extract_structured_notes(input_text, language)
        
        # Parse the JSON result
        try:
            note_data = json.loads(extracted_result)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract manually or return error
            return jsonify({'error': 'Failed to parse generated note structure'}), 500
        
        # Create and save the note
        title = note_data.get('Title', 'Generated Note')
        content = note_data.get('Notes', input_text)
        
        note = Note(title=title, content=content)
        db.session.add(note)
        db.session.commit()
        
        # Return the created note with extracted data
        response_data = note.to_dict()
        response_data['tags'] = note_data.get('Tags', [])
        response_data['original_text'] = input_text
        
        return jsonify(response_data), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

