import os
import secrets
from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Need, Donation
from app.forms import RegistrationForm, LoginForm, NeedForm, DonationForm, UpdateProfileForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Ви успішно увійшли в систему!', 'success')
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
    needs = Need.query.order_by(Need.date_created.desc()).all()
    return render_template('needs.html', needs=needs)

@main.route('/need/<int:need_id>')
def need_detail(need_id):
    need = Need.query.get_or_404(need_id)
    donation_form = DonationForm()
    return render_template('detailed_need.html', need=need, form=donation_form)

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
    
    if form.validate_on_submit():
        donation = Donation(
            amount=form.amount.data,
            donor=current_user,
            need=need
        )

        need.current_amount += form.amount.data
        db.session.add(donation)
        db.session.commit()

        flash(f'Дякуємо за ваш внесок у розмірі {form.amount.data}!', 'success')
        return redirect(url_for('main.need_detail', need_id=need_id))
    
    flash('Виникла помилка з вашим внеском.', 'danger')
    return redirect(url_for('main.need_detail', need_id=need_id))

@main.route('/profile')
@login_required
def profile():
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
    return render_template('profile.html', form=form, now=now)

@main.route('/user/<string:username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    needs = Need.query.filter_by(user_id=user.id).order_by(Need.date_created.desc()).all()
    is_own_profile = False
    if current_user.is_authenticated and current_user.username == username:
        is_own_profile = True
    now = datetime.now()
    return render_template('user_profile.html', user=user, needs=needs, is_own_profile=is_own_profile, now=now)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

def save_need_image(form_picture):
    """Save uploaded need images"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/need_images', picture_fn)
    
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    output_size = (800, 600)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn
