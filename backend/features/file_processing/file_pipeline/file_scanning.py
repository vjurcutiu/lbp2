import os
from db.models import db, File

def scan_and_add_files(path, extensions, conversation_id=None, progress_callback=None):
    """
    Scan a file or directory for files matching the given extensions, add them to the DB.
    Returns dict with added and skipped files.
    """
    added_files = []
    skipped_files = []
    total_files = 0
    processed_files = 0

    if isinstance(extensions, str):
        extensions = [extensions]
    exts = [ext.lower() for ext in extensions]

    if os.path.isfile(path):
        total_files = 1 if any(path.lower().endswith(ext) for ext in exts) else 0
    elif os.path.isdir(path):
        for _, _, files in os.walk(path):
            total_files += sum(1 for f in files if any(f.lower().endswith(ext) for ext in exts))

    def update_progress():
        nonlocal processed_files
        processed_files += 1
        if progress_callback and total_files > 0:
            progress = int((processed_files / total_files) * 100)
            progress_callback(progress)

    if os.path.isfile(path) and any(path.lower().endswith(ext) for ext in exts):
        full_path = os.path.abspath(path)
        existing_file = File.query.filter_by(file_path=full_path).first()
        if existing_file:
            skipped_files.append(full_path)
        else:
            _, file_ext = os.path.splitext(full_path)
            new_file = File(
                file_path=full_path,
                file_extension=file_ext,
                conversation_id=conversation_id,
                is_uploaded=False,
                meta_data=None
            )
            db.session.add(new_file)
            added_files.append(full_path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for filename in files:
                if not any(filename.lower().endswith(ext) for ext in exts):
                    continue
                full_path = os.path.join(root, filename)
                existing_file = File.query.filter_by(file_path=full_path).first()
                if existing_file:
                    skipped_files.append(full_path)
                    continue
                _, file_ext = os.path.splitext(filename)
                new_file = File(
                    file_path=full_path,
                    file_extension=file_ext,
                    conversation_id=conversation_id,
                    is_uploaded=False,
                    meta_data=None
                )
                db.session.add(new_file)
                added_files.append(full_path)
    else:
        raise Exception("Invalid path provided.")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Database error: {e}")

    return {
        'added': added_files,
        'skipped': skipped_files
    }

def scan_and_add_files_wrapper(paths, extension, conversation_id=None, progress_callback=None):
    """
    A wrapper to allow scan_and_add_files to accept either a single file/folder path or a list of paths.
    """
    if isinstance(paths, list):
        aggregated_results = {'added': [], 'skipped': []}
        for path in paths:
            result = scan_and_add_files(path, extension, conversation_id, progress_callback)
            aggregated_results['added'].extend(result.get('added', []))
            aggregated_results['skipped'].extend(result.get('skipped', []))
        return aggregated_results
    else:
        return scan_and_add_files(paths, extension, conversation_id, progress_callback)
