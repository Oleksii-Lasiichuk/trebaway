from app import create_app, db
from app.models import User, Need, Donation, Rating
from flask import render_template
from datetime import datetime
import os

app = create_app()

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Create migrations/versions directory if it doesn't exist
migrations_path = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
if not os.path.exists(migrations_path):
    os.makedirs(migrations_path)
    print(f"Created missing directory: {migrations_path}")

# Uncomment this section to update the database schema with the new 'deleted' column
# Then comment it out again after running the app once
with app.app_context():
    # Check if the column exists
    import sqlite3
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(need)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'deleted' not in columns:
        print("Adding 'deleted' column to the Need table...")
        cursor.execute("ALTER TABLE need ADD COLUMN deleted BOOLEAN DEFAULT 0")
        conn.commit()
        print("Column added successfully!")
    else:
        print("The 'deleted' column already exists in the Need table.")
    
    conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Changed port from 5000 to 5001
