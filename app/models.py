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
    
    # Use primaryjoin to avoid conflicts
    ratings_given = db.relationship('Rating',
                                  foreign_keys="Rating.rater_id",
                                  backref=db.backref('rater', lazy='joined'),
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')
    ratings_received = db.relationship('Rating',
                                     foreign_keys="Rating.rated_user_id",
                                     backref=db.backref('rated_user', lazy='joined'),
                                     lazy='dynamic',
                                     cascade='all, delete-orphan')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

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
    deleted = db.Column(db.Boolean, default=False)
    
    @property
    def percentage_complete(self):
        if self.goal == 0:
            return 0
        return int((self.current_amount / self.goal) * 100)
        
    @property
    def unit(self):
        return "грн"  # Replace with actual unit logic if needed
        
    def __repr__(self):
        return f"Need('{self.title}', '{self.description}')"

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date_donated = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    need_id = db.Column(db.Integer, db.ForeignKey('need.id'), nullable=False)
    
    def __repr__(self):
        return f"Donation('{self.amount}', '{self.date_donated}')"

class Rating(db.Model):
    __tablename__ = 'rating'  # Explicitly name the table
    
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    review = db.Column(db.Text, nullable=True)  # Optional review text
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys with explicit names
    rater_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_rater_id'), nullable=False)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_rated_user_id'), nullable=False)
    
    def __repr__(self):
        return f"Rating({self.rating}, User {self.rater_id} -> User {self.rated_user_id})"
