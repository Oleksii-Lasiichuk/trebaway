from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_login import current_user
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

class UpdateProfileForm(FlaskForm):
    name = StringField('Повне ім\'я', validators=[Length(min=2, max=100)])
    username = StringField('Ім\'я користувача', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Про мене', validators=[Length(max=500)])
    phone = StringField('Телефон', validators=[Length(max=20)])
    location = StringField('Місто', validators=[Length(max=100)])
    image = FileField('Фото профілю', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Зберегти зміни')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Це ім\'я користувача вже зайняте. Будь ласка, оберіть інше.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Цей email вже зареєстрований. Будь ласка, використайте інший.')
