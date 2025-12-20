# newZRL/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange

class UserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    profile_id = StringField('Zwift Profile ID', validators=[DataRequired()]) # Keep as string for now, convert to int in view
    role = SelectField('Ruolo', choices=[('user', 'Utente'), ('captain', 'Capitano'), ('admin', 'Admin')], validators=[DataRequired()])
    active = BooleanField('Attivo', default=True)
    submit = SubmitField('Crea Utente')
