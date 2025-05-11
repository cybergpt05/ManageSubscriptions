from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,SelectField,TextAreaField
from wtforms.validators import DataRequired,Email,Length
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user

class UpdateProfileForm(FlaskForm):
    profile_image = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    api_token = StringField('API Token', render_kw={'readonly': True})
    plan = StringField('Subscription Plan', render_kw={'readonly': True})
    submit = SubmitField('Update Profile')

class AddSubscriberForm(FlaskForm):
    user_id = StringField('Subscriber Id', validators=[DataRequired()])
    plan_id = SelectField('Plan', validators=[DataRequired()])
    start_date = StringField('Start Date')
    end_date = StringField('End Date')
    active = SelectField('Active Status', validators=[DataRequired()], choices=[('True','Active'), ('False','Expired')])
    meta_data = TextAreaField('Meta Data', validators=[Length(max=400)])
    submit = SubmitField('Add Subscriber')
    def __init__(self, *args, **kwargs):
        super(AddSubscriberForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            self.plan_id.choices = [(plan.name, plan.name + ' | ' + str(plan.duration_days) + ' days') for plan in current_user.plans]
        else:
            self.plan_id.choices = []

class AddPlanForm(FlaskForm):
    name = StringField('Plan name', validators=[DataRequired()])
    duration_days = StringField('Duration days', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=300)])
    submit = SubmitField('Add Plan')