from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField
from wtforms.validators import DataRequired,Email,Length

class SupportForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[Length(max=200), DataRequired()])
    submit = SubmitField('Send Message')

class CustomPlan(FlaskForm):
    requests = StringField('Requests Per Month', validators=[DataRequired()])
    subscribers = StringField('Subscribers Limit', validators=[DataRequired()])
    submit = SubmitField('Subscribe')