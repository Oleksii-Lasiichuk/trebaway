from app import create_app, db
from app.models import User, Need, Donation
from flask import render_template
from datetime import datetime

app = create_app()


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

with app.app_context():
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
