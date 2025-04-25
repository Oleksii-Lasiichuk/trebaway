from app import create_app, db
from app.models import User, Need, Donation, Rating  # Add Rating here
from flask import render_template
from datetime import datetime

app = create_app()


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Uncomment these lines temporarily to update the database schema with the new 'deleted' column
# After running the app once, comment them out again to avoid losing data
# with app.app_context():
#     db.drop_all()
#     db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
