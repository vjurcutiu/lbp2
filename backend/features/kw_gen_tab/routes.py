from flask import Blueprint, jsonify
from db.models import File

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
