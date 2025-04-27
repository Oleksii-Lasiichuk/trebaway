from app import db, create_app
from app.models import User, Need
from sqlalchemy import inspect
import sys

def add_column_if_not_exists(table_name, column_name, column_type):
    """Додає нову колонку до таблиці, якщо вона не існує"""
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name not in columns:
            print(f"Додавання колонки {column_name} до таблиці {table_name}...")
            column_type_str = str(column_type).replace("()", "")
            db.session.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_str}')
            db.session.commit()
            print(f"Колонку {column_name} успішно додано!")
        else:
            print(f"Колонка {column_name} вже існує в таблиці {table_name}.")
        
        # Оновлюємо значення за замовчуванням для наявної колонки is_admin
        if table_name == 'user' and column_name == 'is_admin':
            # Встановлюємо всі значення is_admin як False, якщо вони NULL
            db.session.execute(f"UPDATE user SET is_admin = 0 WHERE is_admin IS NULL")
            db.session.commit()
            print("Значення is_admin оновлено для всіх користувачів.")

def ensure_admin_exists():
    """Переконується, що користувач admin існує та має права адміністратора"""
    app = create_app()
    with app.app_context():
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Створення адміністратора...")
            admin = User(
                username='admin',
                email='admin@trebaway.com',
                password=generate_password_hash('your_secure_password'),
                name='Admin',
                surname='Trebaway',
                status='Need',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Адміністратора створено!")
        elif not admin.is_admin:
            print("Надання прав адміністратора існуючому користувачу admin...")
            admin.is_admin = True
            db.session.commit()
            print("Права адміністратора надано!")
        else:
            print("Адміністратор вже існує.")

if __name__ == '__main__':
    # Додаємо колонку is_admin до таблиці user
    add_column_if_not_exists('user', 'is_admin', db.Boolean())
    
    # Перевіряємо та створюємо адміністратора, якщо потрібно
    ensure_admin_exists()
    
    print("Міграцію бази даних успішно завершено!")
    sys.exit(0)
