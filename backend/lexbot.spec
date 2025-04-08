import os
import pinecone
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
eventlet_hidden = collect_submodules("eventlet")
dns_hidden = collect_submodules("dns")
db_hidden = collect_submodules('db')
routes_hidden = collect_submodules('routes')
utils_hidden = collect_submodules('utils')
flask_socketio_hidden = collect_submodules('flask_socketio')
openai_hidden = collect_submodules('openai')





# Automatically gather all data files from the pinecone package.
pinecone_datas = collect_data_files('pinecone')

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    # Merge the collected pinecone data with any other data files you may have.
    datas=pinecone_datas,
    hiddenimports=[
        'db.models',
        'routes.chat_routes',
        'routes.file_processing_routes',
        'routes.extra_routes',
        'routes.info_routes',
        'utils.websockets.sockets',
        'utils.emitters',
        'socketio',
        'eventlet',
        'eventlet.hubs.epolls',
        'eventlet.hubs.kqueue',
        'eventlet.hubs.selects',
        'dns',
        'dns.rdtypes',
        'engineio',
        'flask_socketio',
        'numpy'
    ] + eventlet_hidden
      + dns_hidden
      + db_hidden 
      + routes_hidden 
      + utils_hidden
      + flask_socketio_hidden 
      + openai_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='lexbot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
