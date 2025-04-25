from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate  # Add this line
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Add this line

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Add this line
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Будь ласка, увійдіть для доступу до цієї сторінки.'
    login_manager.login_message_category = 'info'

    # Import and register the blueprint
    from app.routes.main import main
    app.register_blueprint(main)

    return app
