from flask import Flask
from db.models import db

from routes.chat_routes import chat_bp
from routes.file_processing_routes import file_bp
from routes.extra_routes import extra_bp


from flask_migrate import Migrate
from flask_cors import CORS  # Import CORS


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rag_chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)  # Enable CORS for all routes

# Register the chat blueprint
app.register_blueprint(chat_bp, url_prefix='/conversation')
app.register_blueprint(file_bp, url_prefix='/files')
app.register_blueprint(extra_bp, url_prefix='/extra')


if __name__ == '__main__':
    app.run(debug=True)
