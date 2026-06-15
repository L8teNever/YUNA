from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = "yuna-secret-key-change-in-production"
    socketio.init_app(app, async_mode="threading", cors_allowed_origins="*")
    return app
