from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import inspect

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки.'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ваш_секретний_ключ'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    
    from app.routes.main import main
    app.register_blueprint(main)
    
    with app.app_context():
        # Створюємо таблиці, якщо вони не існують
        db.create_all()
        
    return app
