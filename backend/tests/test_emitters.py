import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from flask import Flask
from db.models import db, Conversation
from utils.websockets import sockets
from utils.emitters import emitters  # This registers the event listener

@pytest.fixture
def app():
    app = Flask('test_emitters')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    # Use the existing db instance from db.models
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_after_insert_emits_events(app, mocker):
    # Mock socketio.emit
    emit_mock = mocker.patch.object(sockets.socketio, 'emit')

    # Add a test conversation using the imported Conversation model
    with app.app_context():
        test_conv = Conversation(title="Test", meta_data={"foo": "bar"})
        db.session.add(test_conv)
        db.session.commit()

        # Check that 'conversation_list' and 'new_conversation' were emitted
        assert emit_mock.call_count == 2

        # Extract emitted event names
        emitted_events = [call.args[0] for call in emit_mock.call_args_list]
        assert 'conversation_list' in emitted_events
        assert 'new_conversation' in emitted_events
