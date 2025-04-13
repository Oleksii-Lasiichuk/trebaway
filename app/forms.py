from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, SelectField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    name = StringField('Імʼя', validators=[DataRequired()])
    surname = StringField('Прізвище', validators=[DataRequired()])
    username = StringField('Імʼя користувача', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm = PasswordField('Повторіть пароль', validators=[DataRequired(), EqualTo('password')])
    status = SelectField('Тип користувача', choices=[('Donor', 'Донор'), ('Need', 'Потребую допомоги')], default='Donor')
    submit = SubmitField('Зареєструватися')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Це імʼя користувача вже зайняте. Будь ласка, виберіть інше.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ця електронна пошта вже зареєстрована. Будь ласка, використайте іншу.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Увійти')

class NeedForm(FlaskForm):
    title = StringField('Назва потреби', validators=[DataRequired()])
    description = TextAreaField('Опис', validators=[DataRequired()])
    goal = FloatField('Необхідна кількість', validators=[DataRequired()])
    unit = StringField('Одиниця виміру (шт, грн, тощо)', validators=[DataRequired()])
    region = StringField('Область', validators=[DataRequired()])
    location = StringField('Місце розташування')
    urgency = SelectField('Терміновість', choices=[
        ('Normal', 'Звичайна'), 
        ('Urgent', 'Термінова'), 
        ('Critical', 'Критична')
    ])
    image = FileField('Зображення')
    submit = SubmitField('Створити')

class DonationForm(FlaskForm):
    amount = FloatField('Кількість', validators=[DataRequired()])
    submit = SubmitField('Зробити внесок')
