import logging
from flask import Blueprint, request, jsonify
import utils.services.api_vault.secrets as secret_store

# Configure logger to include filename and function name
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

api_vault_bp = Blueprint('api-vault', __name__)

@api_vault_bp.route('/', methods=['GET', 'POST'])
def index():
    """List entries and handle adding/updating secrets."""
    try:
        if request.method == 'POST':
            # Determine payload source: JSON or form data
            if request.is_json:
                data = request.get_json(silent=True) or {}
            else:
                data = request.form.to_dict() or {}
                logger.info('Using form data payload for POST')

            name = data.get('entry_name', '').strip()
            val = data.get('secret_value', '').strip()
            if not name or not val:
                logger.warning('Invalid input: name or value missing')
                return jsonify({'error': 'Both name and value are required.'}), 400

            secret_store.add_secret(name, val)
            logger.info(f"Added/Updated secret: {name}")
            return jsonify({'message': f"Stored '{name}' successfully."}), 200

        # GET: list all entries
        entries = secret_store.list_entries()
        logger.info('Fetched entries list')
        return jsonify({'entries': entries}), 200

    except Exception as e:
        logger.error(f"Error in index(): {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

@api_vault_bp.route('/entry/<name>', methods=['GET'])
def show_entry(name):
    """Show whether a secret exists for the given entry name."""
    try:
        val = secret_store.fetch_secret(name)
        exists = val is not None
        logger.info(f"Checked existence for secret: {name}, exists={exists}")
        return jsonify({'name': name, 'exists': exists}), 200

    except Exception as e:
        logger.error(f"Error in show_entry('{name}'): {e}", exc_info=True)
        return jsonify({'error': 'Error fetching the secret.'}), 500

@api_vault_bp.route('/delete/<name>', methods=['DELETE'])
def delete_entry(name):
    """Delete the specified secret entry."""
    try:
        secret_store.remove_secret(name)
        logger.info(f"Deleted secret: {name}")
        return jsonify({'message': f"Deleted '{name}'."}), 200

    except Exception as e:
        logger.error(f"Error in delete_entry('{name}'): {e}", exc_info=True)
        return jsonify({'error': 'Error deleting the secret.'}), 500
