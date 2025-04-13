from app import create_app, db
from app.models import User, Need, Donation  # Changed Fundraiser to Need
from flask import render_template
from datetime import datetime

app = create_app()

# Add context processor to make current year available in all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
