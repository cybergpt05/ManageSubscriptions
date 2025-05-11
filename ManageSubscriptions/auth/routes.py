from flask import Blueprint
from flask import render_template,url_for,flash,redirect,request,abort
from ManageSubscriptions import db,limiter
from flask_login import login_user,logout_user,current_user,login_required
from werkzeug.security import generate_password_hash,check_password_hash
from ManageSubscriptions.models import Client
from .forms import LoginForm,SignUpForm,ResetPasswordForm,RequestResetPasswordForm
import uuid,secrets
from datetime import datetime,timedelta
from ManageSubscriptions.helpers import send_email


auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login",methods=['GET','POST'])
@limiter.limit("10 per 5 minutes", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboards.my_account'))
    login_form = LoginForm()
    register_form = SignUpForm()
    if request.method == "POST":
        form_type = request.form.get('form_name')
        if form_type == 'login':
            if login_form.validate_on_submit():
                email = login_form.email.data
                password = login_form.password.data
                remember = login_form.remember.data
                user_exists = Client.query.filter_by(email=email).first()
                if user_exists and check_password_hash(user_exists.password_hash, password):
                    if user_exists.confirmed == True:
                        login_user(user_exists, remember=remember)
                        flash('Login successfull.','success')
                        return redirect(url_for('dashboards.my_account'))
                    else:
                        flash('Your account is not confirmed yet, please confirm your account to be able to login','info')
                        return redirect(url_for('auth.login'))
                else:
                    return render_template('login.html',title='Subly - Login And Sign Up', login_form=login_form,register_form=register_form, message='Invalid email or password.', category='error')
        elif form_type == 'register':
            if register_form.validate_on_submit():
                full_name = register_form.full_name.data
                email = register_form.email.data
                password = register_form.password.data
                if Client.query.filter_by(email=email).first():
                    return render_template('login.html',title='Subly - Login And Sign Up', login_form=login_form,register_form=register_form,message='User with this email already exists.',category='error')
                password_hashed = generate_password_hash(password, method='scrypt',salt_length=16)
                token_created_at = datetime.now()
                confirmation_token = str(uuid.uuid4())
                api_token = secrets.token_urlsafe(64)[:64]

                new_client = Client(name=full_name,email=email,password_hash=password_hashed,confirmation_token=confirmation_token,token_created_at=token_created_at,confirmed=False,api_token=api_token,subscription_type='free',role='client')
                body =f'''
Hi {full_name},

Thank you for signing up at Subly.io!

To complete your registration, please confirm your account by clicking the link below:
{url_for('auth.confirm', token=confirmation_token, _external=True)}

Notice that this link is valid for 24 hours only!

If you did not create an account on our platform, please ignore this email.

Best regards,  
The Subly.io Team
'''
                subject = 'Account Confirmation Request'
                email_status = send_email(subject,email,body)
                if email_status:
                    db.session.add(new_client)
                    db.session.commit()
                    return render_template('login.html',title='Subly - Login And Sign Up', login_form=login_form,register_form=register_form,message='Confirmation email was sent to your email address, please check your inbox.',category='info')
                else:
                    return render_template('login.html',title='Subly - Login And Sign Up', login_form=login_form,register_form=register_form,message='Error happened while creating your account, try again later!',category='error')
        else:
            return abort(403)
    return render_template('login.html',title='Subly - Login And Sign Up', login_form=login_form,register_form=register_form)

@auth_bp.route("/confirm/<string:token>",methods=['GET'])
@limiter.limit("3 per 15 minutes", methods=["GET"])
def confirm(token):
    if not current_user.is_authenticated:
        client = Client.query.filter_by(confirmation_token=token).first()
        if client:
            if client.confirmed == False:
                token_age = datetime.now() - client.token_created_at
                if token_age <= timedelta(hours=24):
                    client.confirmed = True
                    client.confirmation_token = None
                    db.session.commit()
                    flash('Account confirmed successfully, you can login now.','success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('Confirmation token is expired, request a new one.','error')
                    return redirect(url_for('dashboards.profile'))
            else:
                flash('Your account is already confirmed.','info')
                return redirect(url_for('dashboards.profile'))
        else:
            flash('Invalid confirmation token.','error')
            return redirect(url_for('auth.login'))
    else:
        flash('You are logged in, please logout before confirming your account','info')
        return redirect(url_for('dashboards.profile'))

@auth_bp.route("/logout",methods=['GET'])
@limiter.limit("3 per minute", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
    

@auth_bp.route("/request_reset",methods=['GET','POST'])
@limiter.limit("1 per 15 minutes", methods=["POST"])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('dashboards.my_account'))
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        client = Client.query.filter_by(email=email).first()
        if client:
            token = str(uuid.uuid4())
            client.reset_token = token
            client.reset_token_created_at = datetime.now()
            subject = 'Subly - Password Reset Request'
            body = f'''
Dear { client.name },

We received a request to reset your password.  
You can reset it by clicking the link below:

{ url_for('auth.reset_password', token=token, _external=True) }

If you did not request this, please secure your account immediately by changing your password and reviewing recent activity.

Best regards,  
Subly Team

'''
            try:
                db.session.commit()
                send_email(subject,email,body)
                return render_template('request_reset_password.html', title='Subly - Request Reset', form=form, message='We\'ve sent instructions to reset your password to your email, please check your inbox.', category='success')
            except:
                try:
                    client.reset_token = None
                    db.session.commit()
                except:
                    pass
                return render_template('request_reset_password.html', title='Subly - Request Reset', form=form, message='We\'ve countered problems resetting your password, please contact us to help you.', category='error')
        else:
            flash('There is no account associated with this email.','info')
            return redirect(url_for('auth.login'))
    return render_template('request_reset_password.html', title='Subly - Request Request Reset', form=form)


@auth_bp.route("/reset_password/<string:token>",methods=['GET','POST'])
@limiter.limit("10 per 15 minutes", methods=["POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboards.my_account'))
    form = ResetPasswordForm()
    client = Client.query.filter_by(reset_token=token).first()
    if client:
        if client.reset_token_created_at:
            token_age = datetime.now() - client.reset_token_created_at
            if not (token_age <= timedelta(minutes=15)):
                flash('Token expired, please request a new one.','info')
                return redirect(url_for('auth.request_reset'))
        else:
            flash('Invalid token.','error')
            return redirect(url_for('auth.request_reset'))
    else:
        flash('Invalid token.','error')
        return redirect(url_for('auth.request_reset'))
    if form.validate_on_submit():
        password = form.password.data
        client = Client.query.filter_by(reset_token=token).first()
        if client:
            if client.reset_token_created_at:
                token_age = datetime.now() - client.reset_token_created_at
                if token_age <= timedelta(minutes=15):
                    if check_password_hash(client.password_hash,password):
                        flash('Your new password cannot be the same as your current password', 'info')
                        return redirect(url_for('auth.reset_password', token=token))
                    password_hash = generate_password_hash(password, method='scrypt',salt_length=16)
                    if request.headers.getlist("X-Forwarded-For"):
                        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
                    else:
                        ip = request.remote_addr
                    subject = 'Subly- Password Changed'
                    current_time = str(datetime.now()).split('.')[0].split()[1]
                    if ip:
                        client.ip_changed_password = ip
                        body = f'''
Hi { client.name },

We wanted to let you know that your password on Subly.io was successfully changed.

If this was you, no further action is needed.

If this wasn't you, please reset your password immediately and review your account activity.

Here are the details of the action:
• IP Address: { ip }
• Time: { current_time }

Stay safe,  
The Subly.io Team
'''
                    else:
                        body = f'''
Hi { client.name },

We wanted to let you know that your password on Subly.io was successfully changed.

If this was you, no further action is needed.

If this wasn't you, please reset your password immediately and review your account activity.

Here are the details of the action:
• Time: { current_time }

Stay safe,  
The Subly.io Team
'''
                    user_email = client.email
                    
                    try:
                        send_email(subject,user_email,body)
                        client.password_hash = password_hash
                        client.reset_token = None
                        db.session.commit()
                        flash('Your password was changed successfully!','success')
                        return redirect(url_for('auth.login'))
                    except:
                        flash('We\'ve countered problems resetting your password, please contact us to help you.','error')
                        return redirect(url_for('auth.login'))
                else:
                    flash('Token expired, please request a new one.','info')
                    return redirect(url_for('auth.request_reset'))
            else:
                flash('Invalid token.','error')
                return redirect(url_for('auth.request_reset'))
    return render_template('reset_password.html', title='Subly - Reset Password', form=form)
