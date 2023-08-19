from flask_pymongo import PyMongo
from flask import Flask
from flask import sessions
import os
from flask_wtf import CSRFProtect

def create_app():
    app = Flask(__name__)
    app.config['SESSION_TYPE'] = 'filesystem'
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY

    # for push notifications if/when I implement them
    # app.config['VAPID_PRIVATE_KEY'] = os.getenv("VAPID_PRIVATE_KEY")
    # app.config['VAPID_CLAIM_EMAIL'] = os.getenv("VAPID_CLAIM_EMAIL")
    # app.config['VAPID_PUBLIC_KEY'] = os.getenv("VAPID_PUBLIC_KEY")

    csrf = CSRFProtect()
    csrf.init_app(app)

    with app.app_context():
        from .database import db
        from .cache import initialize_cache
        from .views import views
        from .api import api
        
        initialize_cache(app)

        app.register_blueprint(views, url_prefix='/')
        app.register_blueprint(api, url_prefix='/api')
        
    return app