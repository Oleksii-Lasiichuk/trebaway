import os
from app import create_app, db
import shutil

app = create_app()

with app.app_context():
    try:
        # Check if migrations directory exists
        migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_path):
            print("Creating migrations directory...")
            os.makedirs(migrations_path)
        
        # Check if versions directory exists
        versions_path = os.path.join(migrations_path, 'versions')
        if not os.path.exists(versions_path):
            print("Creating versions directory...")
            os.makedirs(versions_path)
        
        print("Migrations directories are set up.")
        
        # Create empty __init__.py files if they don't exist
        init_file = os.path.join(migrations_path, '__init__.py')
        if not os.path.exists(init_file):
            open(init_file, 'w').close()
            print(f"Created {init_file}")
        
        versions_init = os.path.join(versions_path, '__init__.py')
        if not os.path.exists(versions_init):
            open(versions_init, 'w').close()
            print(f"Created {versions_init}")
        
        print("Successfully initialized migrations structure.")
        print("\nNow you can run:")
        print("flask db init")
        print("flask db migrate -m 'Initial migration'")
        print("flask db upgrade")
        
    except Exception as e:
        print(f"Error initializing migrations: {e}")
