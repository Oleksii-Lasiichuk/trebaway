from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app.models import User, Rating
from app import db

main = Blueprint('main', __name__)

@main.route('/user/<username>/edit-rating', methods=['POST'])
@login_required
def edit_rating(username):
    user = User.query.filter_by(username=username).first_or_404()
    rating_id = request.form.get('rating_id')
    stars = request.form.get('stars')
    text = request.form.get('text')
    
    if not rating_id or not stars or not text:
        flash('Всі поля повинні бути заповнені', 'danger')
        return redirect(url_for('main.user_profile', username=username))
        
    rating = Rating.query.get_or_404(rating_id)
    
    # Перевірка, що поточний користувач є автором відгуку
    if current_user.id != rating.rater_id:
        flash('Ви не маєте прав редагувати цей відгук', 'danger')
        return redirect(url_for('main.user_profile', username=username))
    
    rating.stars = stars
    rating.text = text
    db.session.commit()
    
    flash('Ваш відгук успішно оновлено', 'success')
    return redirect(url_for('main.user_profile', username=username))