from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, URL, Optional
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
    goal = FloatField('Необхідна сума', validators=[DataRequired()])
    region = SelectField('Область', choices=[
        ('', 'Виберіть область'),
        ('vinnytsia', 'Вінницька'),
        ('volynska', 'Волинська'),
        ('dnipro', 'Дніпропетровська'),
        ('donetsk', 'Донецька'),
        ('zhytomyr', 'Житомирська'),
        ('zakarpattia', 'Закарпатська'),
        ('zaporizhia', 'Запорізька'),
        ('ivano-frankivsk', 'Івано-Франківська'),
        ('kyiv', 'Київська'),
        ('kirovohrad', 'Кіровоградська'),
        ('luhansk', 'Луганська'),
        ('lviv', 'Львівська'),
        ('mykolaiv', 'Миколаївська'),
        ('odesa', 'Одеська'),
        ('poltava', 'Полтавська'),
        ('rivne', 'Рівненська'),
        ('sumy', 'Сумська'),
        ('ternopil', 'Тернопільська'),
        ('kharkiv', 'Харківська'),
        ('kherson', 'Херсонська'),
        ('khmelnytskyi', 'Хмельницька'),
        ('Черкаська', 'Черкаська'),
        ('chernivtsi', 'Чернівецька'),
        ('chernihiv', 'Чернігівська'),
    ])
    location = StringField('Місце розташування')
    urgency = SelectField('Терміновість', choices=[
        ('Normal', 'Звичайна'), 
        ('Urgent', 'Термінова'), 
        ('Critical', 'Критична')
    ])
    monobank_url = StringField('Посилання на MonoBank', validators=[Optional(), URL(message='Будь ласка, введіть правильну URL адресу')])
    image = FileField('Зображення')
    submit = SubmitField('Створити')

class DonationForm(FlaskForm):
    amount = FloatField('Кількість', validators=[DataRequired()])
    submit = SubmitField('Зробити внесок')
    monobank_submit = SubmitField('Задонатити через MonoBank')
    
    def set_max_amount(self, need):
        """Set maximum allowed donation amount based on the need."""
        self.max_allowed = need.remaining_amount
        self.unit = need.unit
    
    def validate_amount(self, amount):
        """Validate that donation doesn't exceed the remaining goal amount."""
        if hasattr(self, 'max_allowed') and amount.data > self.max_allowed:
            raise ValidationError(f'Ви не можете внести більше, ніж потрібно. Максимальна сума: {self.max_allowed:.2f} {self.unit}')

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
