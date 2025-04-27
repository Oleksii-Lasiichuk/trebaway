import os
import secrets
from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
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
        flash('Ваш акаунт успішно створено!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

# Функція для перевірки, чи користувач є адміністратором
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Доступ заборонено. Ця сторінка доступна тільки для адміністраторів.', 'danger')
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
            # Перевірка на блокування користувача
            if hasattr(user, 'is_blocked') and user.is_blocked:
                flash('Ваш акаунт заблоковано. Зверніться до адміністратора.', 'danger')
                return redirect(url_for('main.login'))
                
            login_user(user)
            next_page = request.args.get('next')
            flash('Ви успішно увійшли в систему!', 'success')
            
            # Якщо користувач - адмін, показуємо додаткове повідомлення
            if user.is_admin:
                flash('Ви увійшли як адміністратор. Доступ до панелі адміністратора через меню.', 'info')
                
            return redirect(next_page if next_page else url_for('main.needs'))
        else:
            flash('Вхід не вдався. Перевірте email і пароль.', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/needs')
def needs():
    needs = Need.query.filter_by(deleted=False).order_by(Need.date_created.desc()).all()
    now = datetime.now()
    return render_template('needs.html', needs=needs, now=now)

@main.route('/need/<int:need_id>')
def need_detail(need_id):
    need = Need.query.get_or_404(need_id)
    form = DonationForm()
    
    # Set maximum donation amount for form validation
    form.set_max_amount(need)
    
    now = datetime.now()
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
            monobank_url=form.monobank_url.data,
            creator=current_user
        )

        if form.image.data:
            image_filename = save_need_image(form.image.data)
            need.image_url = image_filename
        
        db.session.add(need)
        db.session.commit()
        flash('Вашу потребу успішно створено!', 'success')
        return redirect(url_for('main.needs'))
    return render_template('create_need.html', form=form)

@main.route('/donate/<int:need_id>', methods=['POST'])
@login_required
def donate(need_id):
    need = Need.query.get_or_404(need_id)
    form = DonationForm()
    
    # Set maximum donation amount
    form.set_max_amount(need)
    
    if form.validate_on_submit():
        # Additional check just to be safe
        if form.amount.data > need.remaining_amount:
            flash(f'Максимально допустима сума: {need.remaining_amount:.2f} {need.unit}', 'danger')
            return redirect(url_for('main.need_detail', need_id=need_id))
            
        donation = Donation(
            amount=form.amount.data,
            donor=current_user,
            need=need
        )

        need.current_amount += form.amount.data
        db.session.add(donation)
        db.session.commit()

        flash(f'Дякуємо за ваш внесок у розмірі {form.amount.data:.2f} {need.unit}!', 'success')
        return redirect(url_for('main.need_detail', need_id=need_id))
    
    # Display validation errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{error}", 'danger')
    
    return redirect(url_for('main.need_detail', need_id=need_id))

@main.route('/donate_monobank/<int:need_id>', methods=['POST'])
@login_required
def donate_monobank(need_id):
    need = Need.query.get_or_404(need_id)
    
    # Перевіряємо наявність URL MonoBank перед обробкою
    if not need.monobank_url:
        flash('На жаль, посилання на MonoBank не вказано для цього збору.', 'danger')
        return redirect(url_for('main.need_detail', need_id=need_id))

    # Отримуємо суму з прихованого поля форми
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Будь ласка, введіть коректну суму.', 'danger')
        return redirect(url_for('main.need_detail', need_id=need_id))

    if amount <= 0:
        flash('Сума донату повинна бути більше нуля.', 'danger')
        return redirect(url_for('main.need_detail', need_id=need_id))
        
    # Перевірка, чи не перевищує сума залишок
    if amount > need.remaining_amount:
        flash(f'Максимально допустима сума: {need.remaining_amount:.2f} {need.unit}', 'danger')
        return redirect(url_for('main.need_detail', need_id=need_id))
            
    # Створюємо запис про донат
    donation = Donation(
        amount=amount,
        donor=current_user,
        need=need
    )

    need.current_amount += amount
    db.session.add(donation)
    db.session.commit()

    flash(f'Дякуємо за ваш внесок через MonoBank у розмірі {amount:.2f} {need.unit}! Вас буде перенаправлено для оплати.', 'success')
    
    # Перенаправляємо на URL MonoBank
    return redirect(need.monobank_url)

@main.route('/profile')
@login_required
def profile():
    # Якщо користувач - адмін, показуємо посилання на адмін-панель
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
        flash('Ваш профіль успішно оновлено!', 'success')
        return redirect(url_for('main.user_profile', username=current_user.username))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.phone.data = current_user.phone
        form.location.data = current_user.location
    now = datetime.now()
    return render_template('edit_profile.html', form=form, now=now)

@main.route('/user/<string:username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get active (not deleted) needs for the user
    needs = Need.query.filter_by(user_id=user.id, deleted=False).order_by(Need.date_created.desc()).all()
    
    is_own_profile = False
    if current_user.is_authenticated and current_user.username == username:
        is_own_profile = True
    
    # Get ratings data with safer handling of None values
    rating_query = db.session.query(func.avg(Rating.rating).label('average'), 
                                   func.count(Rating.id).label('count')) \
                           .filter(Rating.rated_user_id == user.id).first()
    
    avg_rating = 0
    if rating_query.average is not None:
        avg_rating = round(float(rating_query.average), 1)
    
    rating_count = rating_query.count or 0
    
    # Check if current user has already rated this user
    user_rating = None
    can_rate = False
    
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(rater_id=current_user.id, rated_user_id=user.id).first()
        # Can rate if not self and not already rated or can edit their rating
        can_rate = current_user.id != user.id
    
    # Get reviews for this user
    reviews = Rating.query.filter_by(rated_user_id=user.id).order_by(Rating.date_created.desc()).all()
    
    now = datetime.now()
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
    # Ensure the user is not rating themselves
    if current_user.id == user_id:
        flash('Ви не можете оцінити самі себе!', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    # Check if user has already rated this user
    existing_rating = Rating.query.filter_by(
        rater_id=current_user.id, 
        rated_user_id=user_id
    ).first()
    
    rating_value = int(request.form.get('rating'))
    review_text = request.form.get('review')
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_value
        existing_rating.review = review_text
        flash('Ваша оцінка була оновлена!', 'success')
    else:
        # Create new rating
        new_rating = Rating(
            rating=rating_value,
            review=review_text,
            rater_id=current_user.id,
            rated_user_id=user.id
        )
        db.session.add(new_rating)
        flash('Дякуємо за вашу оцінку!', 'success')
    
    db.session.commit()
    return redirect(url_for('main.user_profile', username=user.username))

@main.route('/delete_need/<int:need_id>', methods=['POST'])
@login_required
def delete_need(need_id):
    need = Need.query.get_or_404(need_id)
    
    # Check if current user is the creator of the need
    if need.user_id != current_user.id:
        flash('Ви не можете видалити цей збір.', 'danger')
        return redirect(url_for('main.need_detail', need_id=need_id))
    
    # Mark as deleted instead of removing from database
    need.deleted = True
    db.session.commit()
    
    flash('Збір успішно видалено.', 'success')
    return redirect(url_for('main.profile'))

# Новий маршрут для адмін-панелі
@main.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    needs = Need.query.all()
    total_donations = db.session.query(func.sum(Donation.amount)).scalar() or 0
    
    return render_template('admin_panel.html', 
                          users=users, 
                          needs=needs, 
                          total_donations=total_donations,
                          now=datetime.now())

# Маршрут для блокування/розблокування користувачів
@main.route('/admin/toggle_user/<int:user_id>')
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    # Перевірка на блокування самого адміністратора
    if user.is_admin:
        flash('Неможливо заблокувати адміністратора!', 'danger')
        return redirect(url_for('main.admin_panel'))
        
    # Припустимо, ми додали поле is_blocked до моделі User
    user.is_blocked = not user.is_blocked
    db.session.commit()
    
    status = "заблоковано" if user.is_blocked else "розблоковано"
    flash(f'Користувач {user.username} успішно {status}.', 'success')
    return redirect(url_for('main.admin_panel'))

# Маршрут для видалення потреб
@main.route('/admin/delete_need/<int:need_id>')
@login_required
@admin_required
def admin_delete_need(need_id):
    need = Need.query.get_or_404(need_id)
    need.deleted = True
    db.session.commit()
    
    flash(f'Потреба "{need.title}" успішно видалена.', 'success')
    return redirect(url_for('main.admin_panel'))

# Маршрут для підтвердження потреб
@main.route('/admin/approve_need/<int:need_id>')
@login_required
@admin_required
def approve_need(need_id):
    need = Need.query.get_or_404(need_id)
    # Припустимо, ми додали поле is_approved до моделі Need
    need.is_approved = True
    db.session.commit()
    
    flash(f'Потреба "{need.title}" успішно затверджена.', 'success')
    return redirect(url_for('main.admin_panel'))

# Маршрут для відхилення потреб
@main.route('/admin/reject_need/<int:need_id>')
@login_required
@admin_required
def reject_need(need_id):
    need = Need.query.get_or_404(need_id)
    # Припустимо, ми додали поле is_approved до моделі Need
    need.is_approved = False
    db.session.commit()
    
    flash(f'Потреба "{need.title}" відхилена.', 'success')
    return redirect(url_for('main.admin_panel'))

# Оновлюємо логін, щоб встановити is_admin при створенні адміністратора
# Це треба буде виконати один раз при ініціалізації бази даних
@main.route('/initialize_admin')
def initialize_admin():
    # Перевірка, чи існує адмін
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@trebaway.com',
            password=generate_password_hash('your_secure_password'),
            name='Admin',
            surname='Trebaway',
            status='Need',
            is_admin=True  # Встановлюємо флаг адміністратора
        )
        db.session.add(admin)
        db.session.commit()
        flash('Адміністратор успішно створений!', 'success')
    else:
        # Якщо адмін існує, але не має прав, надаємо їх
        if not admin.is_admin:
            admin.is_admin = True
            db.session.commit()
            flash('Права адміністратора оновлені!', 'success')
        else:
            flash('Адміністратор вже існує!', 'info')
    
    return redirect(url_for('main.index'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    
    # Resize image
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

def save_need_image(form_image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    image_fn = random_hex + f_ext
    image_path = os.path.join(current_app.root_path, 'static/need_images', image_fn)
    
    # Ensure the need_images directory exists
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    # Save the image
    form_image.save(image_path)
    
    return image_fn
