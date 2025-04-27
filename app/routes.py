from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Need, Donation
from app.forms import RegistrationForm, LoginForm, NeedForm, DonationForm
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

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
    # Update query to filter out deleted needs
    needs = Need.query.filter_by(deleted=False).order_by(Need.date_created.desc()).all()
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
        # Handle image upload here if implemented
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
        try:
            # Convert to float first to handle larger numbers safely
            amount = float(form.amount.data)
            
            # Check if amount is too large for database
            if amount > 999999999:  # Adjust based on your database field size
                flash('Сума пожертви занадто велика. Будь ласка, зв\'яжіться з нами для великих пожертв.', 'danger')
                return redirect(url_for('main.need_detail', need_id=need.id))
                
            # Create the donation record
            donation = Donation(
                amount=amount,
                need_id=need_id,
                user_id=current_user.id
            )
            
            # Update the need's current amount
            need.current_amount += amount
            
            # Add and commit to database
            db.session.add(donation)
            db.session.commit()
            
            flash('Дякуємо за вашу пожертву!', 'success')
            return redirect(url_for('main.need_detail', need_id=need_id))
            
        except Exception as e:
            # Rollback transaction in case of errors
            db.session.rollback()
            flash(f'Помилка при обробці пожертви. Будь ласка, спробуйте ще раз.', 'danger')
            print(f"Donation error: {str(e)}")  # Log the error
            return redirect(url_for('main.need_detail', need_id=need_id))
    
    flash('Виникла помилка з вашим внеском.', 'danger')
    return redirect(url_for('main.need_detail', need_id=need_id))

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

@main.route('/profile')
@login_required
def profile():
    user_needs = Need.query.filter_by(user_id=current_user.id).order_by(Need.date_created.desc()).all()
    return render_template('profile.html', user=current_user, user_needs=user_needs)