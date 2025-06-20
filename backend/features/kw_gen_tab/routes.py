from flask import Blueprint, jsonify, request
import os
from db.models import File, db

kw_gen_tab_bp = Blueprint('kw_gen_tab', __name__, url_prefix='/files')

@kw_gen_tab_bp.route('/', methods=['GET'])
def get_files():
    files = File.query.all()
    files_data = [
        {
            "id": f.id,
            "file_path": f.file_path,
            "file_extension": f.file_extension,
            "meta_data": f.meta_data or {},
            "conversation_id": f.conversation_id,
            "is_uploaded": f.is_uploaded,
            "created_at": f.created_at.isoformat() if f.created_at else None
        }
        for f in files
    ]
    return jsonify(files_data)

@kw_gen_tab_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    file = File.query.get(file_id)
    if not file:
        return jsonify({"error": "File not found"}), 404

    db.session.delete(file)
    db.session.commit()
    return jsonify({"success": True, "deleted_id": file_id}), 200

@kw_gen_tab_bp.route('/content', methods=['GET'])
def get_file_content():
    path = request.args.get('path')
    if not path or not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500