import os
import secrets
from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Need, Donation, Rating
from app.forms import RegistrationForm, LoginForm, NeedForm, DonationForm, UpdateProfileForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
from functools import wraps

# Create the blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            password=hashed,
            name=form.name.data,
            surname=form.surname.data,
            status=form.status.data
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

# Функція для перевірки, чи користувач є адміністратором
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Перевіряємо, чи користувач автентифікований та чи є адміном
        if not current_user.is_authenticated or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if hasattr(user, 'is_blocked') and user.is_blocked:
                return redirect(url_for('main.login'))
                
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.needs'))
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/needs')
def needs():
    needs = Need.query.filter_by(deleted=False).order_by(Need.date_created.desc()).all()
    now = datetime.now() # Use .now() for local time if needed
    return render_template('needs.html', needs=needs, now=now)

@main.route('/need/<int:need_id>')
def need_detail(need_id):
    need = Need.query.get_or_404(need_id)
    form = DonationForm()
    
    if hasattr(form, 'set_max_amount'):
        form.set_max_amount(need)
    
    now = datetime.now() # Use .now() for local time if needed
    return render_template('detailed_need.html', need=need, form=form, now=now)

@main.route('/create_need', methods=['GET', 'POST'])
@login_required
def create_need():
    form = NeedForm()
    if form.validate_on_submit():
        need = Need(
            title=form.title.data,
            description=form.description.data,
            goal=form.goal.data,
            region=form.region.data,
            location=form.location.data,
            urgency=form.urgency.data,
            monobank_url=form.monobank_url.data if hasattr(form, 'monobank_url') else None,
            creator=current_user
        )

        if hasattr(form, 'image') and form.image.data:
            image_filename = save_need_image(form.image.data)
            need.image_url = image_filename
        
        db.session.add(need)
        db.session.commit()
        return redirect(url_for('main.needs'))
    return render_template('create_need.html', form=form)

@main.route('/donate/<int:need_id>', methods=['POST'])
@login_required
def donate(need_id):
    need = Need.query.get_or_404(need_id)
    form = DonationForm()
    
    if hasattr(form, 'set_max_amount'):
        form.set_max_amount(need)
    
    if form.validate_on_submit():
        try:
            amount = float(form.amount.data)

            if amount > 999999999:
                return redirect(url_for('main.need_detail', need_id=need_id))

            if hasattr(need, 'remaining_amount') and amount > need.remaining_amount:
                return redirect(url_for('main.need_detail', need_id=need_id))
            
            donation_args = {'amount': amount}
            if hasattr(Donation, 'donor'):
                donation_args['donor'] = current_user
                donation_args['need'] = need
            else:
                donation_args['user_id'] = current_user.id
                donation_args['need_id'] = need_id
            
            donation = Donation(**donation_args)
            
            need.current_amount += amount
            db.session.add(donation)
            db.session.commit()
            
            return redirect(url_for('main.need_detail', need_id=need_id))

        except ValueError:
             return redirect(url_for('main.need_detail', need_id=need_id))
        except Exception as e:
            db.session.rollback()
            print(f"Donation error: {str(e)}")
            return redirect(url_for('main.need_detail', need_id=need_id))
    
    return redirect(url_for('main.need_detail', need_id=need_id))

@main.route('/donate_monobank/<int:need_id>', methods=['POST'])
@login_required
def donate_monobank(need_id):
    need = Need.query.get_or_404(need_id)
            
    if not hasattr(need, 'monobank_url') or not need.monobank_url:
        return redirect(url_for('main.need_detail', need_id=need_id))
    
    try:
        amount = float(request.form.get('amount', 0))
        
        if amount <= 0:
            return redirect(url_for('main.need_detail', need_id=need_id))
        
        if amount > 999999999:
            return redirect(url_for('main.need_detail', need_id=need_id))
            
        if hasattr(need, 'remaining_amount') and amount > need.remaining_amount:
            return redirect(url_for('main.need_detail', need_id=need_id))
                
        donation_args = {'amount': amount}
        if hasattr(Donation, 'donor'):
            donation_args['donor'] = current_user
            donation_args['need'] = need
        else:
            donation_args['user_id'] = current_user.id
            donation_args['need_id'] = need_id
            
        donation = Donation(**donation_args)

        need.current_amount += amount
        db.session.add(donation)
        db.session.commit()

        return redirect(need.monobank_url)
    
    except ValueError:
        return redirect(url_for('main.need_detail', need_id=need_id))
    except Exception as e:
        db.session.rollback()
        print(f"MonoBank donation error: {str(e)}")
        return redirect(url_for('main.need_detail', need_id=need_id))

@main.route('/profile')
@login_required
def profile():
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return render_template('admin_profile.html', user=current_user, now=datetime.now())
        
    return redirect(url_for('main.user_profile', username=current_user.username))

@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
            current_user.image = picture_file
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        current_user.phone = form.phone.data
        current_user.location = form.location.data
        db.session.commit()
        return redirect(url_for('main.user_profile', username=current_user.username))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.phone.data = current_user.phone
        form.location.data = current_user.location
        
    now = datetime.now() # Use .now() for local time if needed
    return render_template('edit_profile.html', form=form, now=now)

@main.route('/user/<string:username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    needs = Need.query.filter_by(user_id=user.id, deleted=False).order_by(Need.date_created.desc()).all()
    
    is_own_profile = False
    if current_user.is_authenticated and current_user.username == username:
        is_own_profile = True
    
    rating_query = db.session.query(func.avg(Rating.rating).label('average'), 
                                   func.count(Rating.id).label('count')) \
                           .filter(Rating.rated_user_id == user.id).first()
    
    avg_rating = 0.0
    if rating_query and rating_query.average is not None:
        avg_rating = round(float(rating_query.average), 1)
    
    rating_count = rating_query.count if rating_query else 0
    
    user_rating = None
    can_rate = False
    
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(rater_id=current_user.id, rated_user_id=user.id).first()
        can_rate = current_user.id != user.id and user_rating is None
    
    reviews = Rating.query.filter_by(rated_user_id=user.id).order_by(Rating.date_created.desc()).all()
    
    now = datetime.now() # Use .now() for local time if needed
    return render_template('user_profile.html', 
                          user=user, 
                          needs=needs, 
                          is_own_profile=is_own_profile, 
                          avg_rating=avg_rating,
                          rating_count=rating_count,
                          reviews=reviews,
                          user_rating=user_rating, 
                          can_rate=can_rate,
                          now=now)

@main.route('/rate_user/<int:user_id>', methods=['POST'])
@login_required
def rate_user(user_id):
    rating = request.form.get('rating', type=int)
    review = request.form.get('review', '')
    
    if not rating or rating < 1 or rating > 5:
        return redirect(request.referrer or url_for('main.index'))
    
    if current_user.id == user_id:
        return redirect(request.referrer or url_for('main.index'))
        
    user = User.query.get_or_404(user_id)
    
    existing_rating = Rating.query.filter_by(
        rater_id=current_user.id, 
        rated_user_id=user_id
    ).first()
    
    if existing_rating:
        existing_rating.rating = rating
        existing_rating.review = review
        existing_rating.date_created = datetime.utcnow()
    else:
        new_rating = Rating(
            rater_id=current_user.id,
            rated_user_id=user_id,
            rating=rating,
            review=review
        )
        db.session.add(new_rating)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    
    return redirect(url_for('main.user_profile', username=user.username))

@main.route('/delete_need/<int:need_id>', methods=['POST'])
@login_required
def delete_need(need_id):
    need = Need.query.get_or_404(need_id)
    
    is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
    if need.user_id != current_user.id and not is_admin:
        return redirect(url_for('main.need_detail', need_id=need_id))
    
    need.deleted = True
    db.session.commit()
    
    if is_admin:
         return redirect(url_for('main.admin_panel'))
    else:
         return redirect(url_for('main.profile'))

@main.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    needs = Need.query.order_by(Need.date_created.desc()).all() 
    total_donations = db.session.query(func.sum(Donation.amount)).scalar() or 0.0
    
    return render_template('admin_panel.html', 
                          users=users, 
                          needs=needs, 
                          total_donations=total_donations,
                          now=datetime.now())

@main.route('/admin/toggle_user/<int:user_id>')
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if hasattr(user, 'is_admin') and user.is_admin:
        return redirect(url_for('main.admin_panel'))
        
    if hasattr(user, 'is_blocked'):
        user.is_blocked = not user.is_blocked
        db.session.commit()
    return redirect(url_for('main.admin_panel'))    

@main.route('/admin/delete_need/<int:need_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_need(need_id):
    return delete_need(need_id) 

@main.route('/admin/approve_need/<int:need_id>')
@login_required
@admin_required
def approve_need(need_id):
    need = Need.query.get_or_404(need_id)
    if hasattr(need, 'is_approved'):
        need.is_approved = True
        db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main.route('/admin/reject_need/<int:need_id>')
@login_required
@admin_required
def reject_need(need_id):
    need = Need.query.get_or_404(need_id)
    if hasattr(need, 'is_approved'):
        need.is_approved = False
        db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main.route('/initialize_admin')
def initialize_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        try:
            admin = User(
                username='admin',
                email='admin@trebaway.com',
                password=generate_password_hash('your_secure_password'),
                name='Admin',
                surname='Trebaway',
                status='Need',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        except Exception as e:
             db.session.rollback()
             print(f"Admin creation error: {str(e)}")
    else:
        if not hasattr(admin, 'is_admin') or not admin.is_admin:
            try:
                admin.is_admin = True
                db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 print(f"Admin update error: {str(e)}")
    return redirect(url_for('main.index'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    output_size = (150, 150)
    try:
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
    except Exception as e:
        print(f"Error saving picture: {e}")
        return None
        
    return picture_fn

def save_need_image(form_image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    image_fn = random_hex + f_ext
    image_path = os.path.join(current_app.root_path, 'static/need_images', image_fn)
    
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    try:
        form_image.save(image_path)
    except Exception as e:
        print(f"Error saving need image: {e}")
        return None

    return image_fn
