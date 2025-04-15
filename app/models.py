from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Donor")  # 'Donor' or 'Need'
    image = db.Column(db.String(20), nullable=True, default='default.jpg')
    bio = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    needs = db.relationship('Need', backref='creator', lazy=True)
    donations = db.relationship('Donation', backref='donor', lazy=True)

class Need(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    region = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    urgency = db.Column(db.String(50), default="Normal")  # "Normal", "Urgent", "Critical"
    image_url = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    donations = db.relationship('Donation', backref='need', lazy=True)
    
    @property
    def percentage_complete(self):
        if self.goal == 0:
            return 0
        return int((self.current_amount / self.goal) * 100)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date_donated = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    need_id = db.Column(db.Integer, db.ForeignKey('need.id'), nullable=False)
