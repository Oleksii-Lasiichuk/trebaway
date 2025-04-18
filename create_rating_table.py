from app import create_app, db
from app.models import Rating

app = create_app()

with app.app_context():
    # Check if Rating table exists
    inspector = db.inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    if 'rating' not in existing_tables:
        print("Creating Rating table...")
        # Create the Rating table explicitly
        db.create_all(tables=[Rating.__table__])
        print("Rating table created successfully")
    else:
        print("Rating table already exists")
