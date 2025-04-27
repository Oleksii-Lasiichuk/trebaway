import sqlite3
from app import create_app

app = create_app()

def add_monobank_field():
    with app.app_context():
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if monobank_url column exists
        cursor.execute("PRAGMA table_info(need)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'monobank_url' not in columns:
            print("Adding 'monobank_url' column to the Need table...")
            try:
                cursor.execute("ALTER TABLE need ADD COLUMN monobank_url TEXT")
                conn.commit()
                print("Column added successfully!")
            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
        else:
            print("The 'monobank_url' column already exists in the Need table.")
        
        conn.close()

if __name__ == "__main__":
    add_monobank_field()
