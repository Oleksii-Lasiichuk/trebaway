from app import create_app, db
from app.models import User, Need, Donation
from flask import render_template
from datetime import datetime

app = create_app()

# Add context processor to make current year available in all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

with app.app_context():
    # Drop all existing tables and recreate them
    db.drop_all()
    db.create_all()  # Uncommented this line to actually create tables

if __name__ == '__main__':
    # Use the default port 5000 explicitly
    app.run(debug=True, port=5000)
