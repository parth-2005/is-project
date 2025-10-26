# /secure-file-sender/app/__init__.py
from flask import Flask
from .crypto import generate_keys

def create_app():
    # Generate the server's keys on startup
    generate_keys()
    
    app = Flask(__name__)

    # Register the routes from routes.py
    with app.app_context():
        from . import routes

    return app