from app import create_app, db
import sqlite3
import inspect
import sys
from importlib import import_module

app = create_app()

def inspect_database():
    # Get database URI from app config
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    print(f"Database path: {db_path}")
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\nTables in database:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("  Columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    conn.close()

def inspect_sqlalchemy_models():
    print("\nSQLAlchemy models defined in the app:")
    try:
        # Try to import all models
        from app.models import User, Need, Donation, Rating
        
        # List all models and their tablenames
        models = [User, Need, Donation, Rating]
        for model in models:
            print(f"- {model.__name__}")
            print(f"  Table name: {model.__tablename__}")
            print(f"  Primary key: {[pk.name for pk in model.__table__.primary_key.columns]}")
            print("  Columns:")
            for column in model.__table__.columns:
                print(f"    - {column.name}: {column.type}")
        
        # Check if Rating model is properly defined
        print("\nRating model details:")
        print(f"Rating.__table__: {Rating.__table__}")
        print(f"Rating.__tablename__: {Rating.__tablename__ if hasattr(Rating, '__tablename__') else 'Not set'}")
        
        # Check relationships
        print("\nUser model relationships:")
        print(f"- ratings_given: {User.ratings_given.prop}")
        print(f"- ratings_received: {User.ratings_received.prop}")
        
    except (ImportError, AttributeError) as e:
        print(f"Error importing models: {e}")
        import traceback
        traceback.print_exc()

def check_app_imports():
    print("\nChecking app imports...")
    try:
        # Check if the create_app function properly imports models
        from app import create_app
        
        # Check how app imports models
        import app
        module_content = dir(app)
        print(f"App module content: {module_content}")
        
        # Check if Rating is being imported somewhere
        if hasattr(app, 'models'):
            print("Models found in app module")
            if hasattr(app.models, 'Rating'):
                print("Rating class found in app.models")
            else:
                print("Rating class NOT found in app.models")
        else:
            print("Models NOT directly available in app module")
            
        # Check route imports
        try:
            from app.routes import main
            print("Main routes imported successfully")
            route_imports = inspect.getmodule(main).__dict__
            if 'Rating' in route_imports:
                print("Rating model is imported in routes")
            else:
                print("Rating model is NOT imported in routes")
        except ImportError:
            print("Could not import main routes")
            
    except ImportError as e:
        print(f"Error in app imports: {e}")

def check_run_file():
    print("\nChecking run.py file...")
    try:
        # Check what models are imported in run.py
        import run
        run_imports = inspect.getmodule(run).__dict__
        print("Models imported in run.py:")
        for name, obj in run_imports.items():
            if name in ['User', 'Need', 'Donation', 'Rating']:
                print(f"- {name}")
        
        if 'Rating' not in run_imports:
            print("Rating model is NOT imported in run.py")
    except ImportError as e:
        print(f"Error importing run.py: {e}")

if __name__ == "__main__":
    with app.app_context():
        inspect_database()
        inspect_sqlalchemy_models()
        check_app_imports()
        check_run_file()
        
        # Create a script to manually create the Rating table
        print("\nHere's a script to manually create the Rating table:")
        print("""
from app import create_app, db
from app.models import Rating

app = create_app()

with app.app_context():
    # Create only the Rating table
    Rating.__table__.create(db.engine, checkfirst=True)
    print("Rating table created successfully")
        """)
