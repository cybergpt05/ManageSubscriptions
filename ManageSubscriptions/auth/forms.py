from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField,ValidationError
from wtforms.validators import DataRequired,Email,EqualTo

def validate_password_strength(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not any(c.islower() for c in password):
        raise ValidationError('Password must include a lowercase letter.')
    if not any(c.isupper() for c in password):
        raise ValidationError('Password must include an uppercase letter.')
    if not any(c.isdigit() for c in password):
        raise ValidationError('Password must include a number.')
    if not any(c in "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~" for c in password):
        raise ValidationError('Password must include a special character.')

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[Email(),DataRequired()])
    password = PasswordField('Password',validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log in', name='login')

class SignUpForm(FlaskForm):
    full_name = StringField('Full name',validators=[DataRequired()])
    email = StringField('Email',validators=[Email(),DataRequired()])
    password = PasswordField('Password',validators=[DataRequired(),validate_password_strength])
    confirm_password = PasswordField('Confirm password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Sign up', name='register')

class RequestResetPasswordForm(FlaskForm):
    email = StringField('Email',validators=[Email(),DataRequired()])
    submit = SubmitField('Request Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password',validators=[DataRequired(),validate_password_strength])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Reset Password')

