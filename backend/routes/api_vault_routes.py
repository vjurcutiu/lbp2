import logging
from flask import Blueprint, request, render_template, redirect, url_for, flash
import utils.services.api_vault.secrets as secret_store

# Configure logger to include filename and function name
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

routes = Blueprint('api-vault', __name__)

@routes.route('/', methods=['GET', 'POST'])
def index():
    """List entries and handle adding/updating secrets."""
    try:
        if request.method == 'POST':
            name = request.form.get('entry_name', '').strip()
            val = request.form.get('secret_value', '').strip()
            if not name or not val:
                flash('Both name and value are required.', 'warning')
                logger.warning('Invalid input: name or value missing')
                return redirect(url_for('routes.index'))

            secret_store.add_secret(name, val)
            flash(f"Stored '{name}' successfully.", 'success')
            logger.info(f"Added/Updated secret: {name}")
            return redirect(url_for('routes.index'))

        entries = secret_store.list_entries()
        logger.info('Fetched entries list')
        return render_template('index.html', entries=entries)

    except Exception as e:
        flash('An error occurred while processing your request.', 'error')
        logger.error(f"Error in index(): {e}", exc_info=True)
        return render_template('index.html', entries=[]), 500

@routes.route('/entry/<name>', methods=['GET'])
def show_entry(name):
    """Show whether a secret exists for the given entry name."""
    try:
        val = secret_store.fetch_secret(name)
        exists = val is not None
        logger.info(f"Checked existence for secret: {name}, exists={exists}")
        return render_template('entry.html', name=name, exists=exists)

    except Exception as e:
        flash('Error fetching the secret.', 'error')
        logger.error(f"Error in show_entry('{name}'): {e}", exc_info=True)
        return redirect(url_for('routes.index')), 500

@routes.route('/delete/<name>', methods=['POST'])
def delete_entry(name):
    """Delete the specified secret entry."""
    try:
        secret_store.remove_secret(name)
        flash(f"Deleted '{name}'.", 'info')
        logger.info(f"Deleted secret: {name}")
        return redirect(url_for('routes.index'))

    except Exception as e:
        flash('Error deleting the secret.', 'error')
        logger.error(f"Error in delete_entry('{name}'): {e}", exc_info=True)
        return redirect(url_for('routes.index')), 500
