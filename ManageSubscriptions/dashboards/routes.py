from flask import Blueprint
from flask import render_template,url_for,flash,redirect,request,abort
from ManageSubscriptions import db,limiter,app
from flask_login import current_user,login_required
from werkzeug.utils import secure_filename
from ManageSubscriptions.models import ClientSubscriber,APIUsageTrack,Client,ClientPlan
from .forms import UpdateProfileForm,AddSubscriberForm,AddPlanForm
import secrets,hashlib,os
from datetime import datetime,timedelta
from .helpers import generate_usage_chart,calc_file_hash,check_image_security
from ManageSubscriptions.api.helpers import is_valid_date
import requests

dashboards_bp = Blueprint('dashboards', __name__)

@dashboards_bp.route("/my/account",methods=['GET','POST'])
@limiter.limit("50000 per 10 minutes", methods=["POST"])
@login_required
def my_account():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        image = form.profile_image.data
        full_name = form.full_name.data
        email = form.email.data
        try:
            if email != current_user.email:
                is_registered = Client.query.filter_by(email=email).first()
                if is_registered:
                    flash('Email is already taken.', 'error')
                    return redirect(url_for('dashboards.my_account'))
                else:
                    current_user.email = email
            if full_name != current_user.name:
                current_user.name = full_name
            if image != None:
                if not check_image_security(image):
                    flash('Uploaded image isn\'t a real image', 'error')
                    return redirect(url_for('dashboards.my_account'))
                image_name_original = secure_filename(image.filename)
                old_image_hash = None
                old_image = os.path.join(app.root_path, 'static' , 'profile_pics' , current_user.profile_image)
                if os.path.exists(old_image):
                    old_image_hash = calc_file_hash(old_image)
                new_image_hash = hashlib.md5(image.read()).hexdigest()
                image.stream.seek(0)
                if old_image_hash != new_image_hash:
                    if current_user.profile_image != 'default.png':
                        if os.path.exists(old_image):
                            os.remove(old_image)
                    _, ext = os.path.splitext(image_name_original)
                    image_filename = f"{secrets.token_hex(24)}{ext}"
                    current_user.profile_image = image_filename
                    image_path = os.path.join(app.root_path, 'static', 'profile_pics', image_filename)
                    form.profile_image.data.save(image_path)
            db.session.commit()
            flash('Your info was updated successfully.', 'success')
            return redirect(url_for('dashboards.my_account'))
        except:
            flash('Failed tp update your info, contact us to help you.', 'error')
            return redirect(url_for('dashboards.my_account'))
        

    return render_template('my_account.html', title='Subly - My Account', form=form)

@dashboards_bp.route("/my/dashboard",methods=['GET','POST'])
@login_required
def dashboard():
    # catching api logs
    api_usage_this_month = 0
    api_usage_this_day = 0
    graph_dates = []
    graph_requests = []
    graph_file_name = None
    api_usage_logs = APIUsageTrack.query.filter_by(client_id=current_user.id).all()
    if api_usage_logs:
        seven_days_ago = datetime.now().date() - timedelta(days=7)
        today = datetime.now().date()

        for log in api_usage_logs:
            log_date = log.usage_date.date() if isinstance(log.usage_date, datetime) else log.usage_date
            if log_date.month == today.month:
                api_usage_this_month += log.usage_quantity
            if log_date == today:
                api_usage_this_day += log.usage_quantity
            if seven_days_ago < log_date <= today:
                graph_dates.append(log_date.strftime("%Y-%m-%d"))
                graph_requests.append(log.usage_quantity)
        if graph_dates:
            data = {'dates':graph_dates,'requests':graph_requests}
            graph_file_name = generate_usage_chart(data)
            current_chart_image = current_user.api_logs_chart
            if current_chart_image:
                path_to_old_chart = os.path.join(app.root_path, 'static' , 'usage_logs' , current_chart_image)
                if os.path.exists(path_to_old_chart):
                    os.remove(path_to_old_chart)
            current_user.api_logs_chart = graph_file_name
            db.session.commit()
    usage_of_plan = current_user.requests
    plan_requests = current_user.allowed_requests

    # catching subscribers for client
    subscribers = 0
    active_subscribers = 0
    nonactive_subscribers = 0
    grapped_subs = ClientSubscriber.query.filter_by(client_id=current_user.id).all()
    if grapped_subs:
        for sub in grapped_subs:
            if sub.active:
                active_subscribers+=1
            else:
                nonactive_subscribers+=1
            subscribers+=1

    return render_template('dashboard.html', 
                           title='Subly - Dashboard',
                           api_usage_this_month=api_usage_this_month,
                           api_usage_this_day=api_usage_this_day,
                           graph_file_name=graph_file_name,
                           usage_of_plan=usage_of_plan,
                           plan_requests=plan_requests,
                           subscribers=subscribers,
                           active_subscribers=active_subscribers,
                           nonactive_subscribers=nonactive_subscribers,
                           client_plan=current_user.subscription_type,
                           remaining_days=current_user.remaining_days)

@dashboards_bp.route("/my/subscribers",methods=['GET'])
@limiter.limit("30 per 10 minutes", methods=["POST"])
@login_required
def subscribers():
    subscribers = current_user.subscribers
    plans = {}
    if current_user.plans:
        for plan in current_user.plans:
            plans[plan.id] = plan.name
    return render_template('my_subscribers.html', title='Subly - My Subscribers', subscribers=subscribers,plans=plans)

@dashboards_bp.route("/my/subscribers/delete/<string:id>",methods=['GET'])
@login_required
def delete_user(id):
    client_id = current_user.id
    is_subscriber_exists = ClientSubscriber.query.filter_by(client_id=client_id,user_id=id).first()
    if is_subscriber_exists:
        db.session.delete(is_subscriber_exists)
        db.session.commit()
        flash('Subscriber was deleted successfully.', 'success')
        return redirect(url_for('dashboards.subscribers'))
    else:
        flash('You have no subscriber associated with this id.', 'error')
        return redirect(url_for('dashboards.subscribers'))

@dashboards_bp.route("/my/subscribers/add",methods=['GET','POST'])
@login_required
def add_subscriber():
    form = AddSubscriberForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        plan_id = form.plan_id.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        active = form.active.data
        meta_data = form.meta_data.data
        try:
            plan_id = plan_id.split()[0]
        except:
            abort(403)
        is_sub_exists = ClientSubscriber.query.filter_by(client_id=current_user.id,user_id=user_id).first()
        if is_sub_exists:
            flash('User with this id already exists.', 'error')
            return redirect(url_for('dashboards.add_subscriber'))
        if active == 'True':
            active = True
        elif active == 'False':
            active = False
        else:
            flash(f'Invalid active status entry.', 'error')
            return redirect(url_for('dashboards.add_subscriber'))
        if meta_data == '':
            meta_data = None
        data_to_post = {"user_id":user_id,"plan_name":plan_id,"start_date":start_date,"end_date":end_date,"active":active,"meta_data":meta_data}
        if data_to_post['start_date'] == '':
            del data_to_post['start_date']
        if data_to_post['end_date'] == '':
            del data_to_post['end_date']
        print(data_to_post)
        url = url_for('api.api_add_subscriber', _external=True)
        response = requests.post(url, headers={'X-API-KEY':current_user.api_token,'Content-Type':'application/json'}, json=data_to_post)
        if response.status_code == 200:
            flash(f'Subscriber was added successfully.', 'success')
            return redirect(url_for('dashboards.add_subscriber'))
        else:
            error_msg = response.json()["message"]
            flash(error_msg, 'error')
            return redirect(url_for('dashboards.add_subscriber'))

    return render_template('add_subscriber.html', title='Subly - Add Subscriber', form=form)

@dashboards_bp.route("/my/plans",methods=['GET'])
@limiter.limit("30 per 10 minutes", methods=["POST"])
@login_required
def plans():
    plans = current_user.plans
    plans_subscribers = {}
    for plan in plans:
        plans_subscribers[plan.name] = len(plan.subscribers)
    print(plans_subscribers)
    return render_template('my_plans.html', title='Subly - My Plans', plans=plans, plans_subscribers=plans_subscribers)

@dashboards_bp.route("/my/plans/delete/<string:name>",methods=['GET'])
@login_required
def delete_plan(name):
    client_id = current_user.id
    is_plan_exists = ClientPlan.query.filter_by(client_id=client_id,name=name).first()
    if is_plan_exists:
        has_subscribers = ClientSubscriber.query.filter_by(plan_id=is_plan_exists.id).all()
        subscribers_count = len(has_subscribers)
        if has_subscribers:
            for subscriber in has_subscribers:
                db.session.delete(subscriber)
        db.session.delete(is_plan_exists)
        db.session.commit()
        flash(f'Plan and {subscribers_count} subscribers was deleted successfully.', 'success')
        return redirect(url_for('dashboards.plans'))
    else:
        flash('You have no subscriber associated with this id.', 'error')
        return redirect(url_for('dashboards.plans'))

@dashboards_bp.route("/my/plans/add",methods=['GET','POST'])
@login_required
def add_plan():
    form = AddPlanForm()
    if form.validate_on_submit():
        name = form.name.data
        duration_days = form.duration_days.data
        description = form.description.data
        if not name:
            flash('Name cannot be null.', 'error')
            return redirect(url_for('dashboards.add_plan'))
        try:
            int(duration_days)
        except:
            flash('Duration days should be integer.', 'error')
            return redirect(url_for('dashboards.add_plan'))
        if description == "":
            description = None
        is_plan_exists = ClientPlan.query.filter_by(client_id=current_user.id,name=name).first()
        if is_plan_exists:
            flash('This plan already exists.', 'error')
            return redirect(url_for('dashboards.add_plan'))
        data_to_post = {"name":name,"duration_days":int(duration_days),"description":description}
        url = url_for('api.api_add_plan', _external=True)
        response = requests.post(url, headers={'X-API-KEY':current_user.api_token,'Content-Type':'application/json'}, json=data_to_post)
        if response.status_code == 200:
            flash(f'Plan was added successfully.', 'success')
            return redirect(url_for('dashboards.add_plan'))
        else:
            error_msg = response.json()["message"]
            flash(error_msg, 'error')
            return redirect(url_for('dashboards.add_plan'))

    return render_template('add_plan.html', title='Subly - Add Plan', form=form)