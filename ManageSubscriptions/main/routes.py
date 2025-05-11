from flask import Blueprint
from flask import render_template,url_for,flash,redirect,request,abort
from ManageSubscriptions import db,limiter
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route("/",methods=['GET'])
@main_bp.route("/home",methods=['GET'])
def index():
    return render_template('home.html',title='Subly - Manage subscriptions easily')

@main_bp.route('/pricing', methods=["GET","POST"])
@limiter.limit("5 per 10 minutes", methods=["POST"])
def pricing():
    if request.method == "POST":
        try:
            plan = request.form.get('plan')
            if current_user.is_authenticated:
                client = current_user
                if plan =='pro':
                    try:
                        if client.subscription_type == 'pro':
                            flash('Your pro plan has been renewed.','success')
                        else:
                            flash('You are now a pro user.','success')
                        client.subscription_type = 'pro'
                        client.remaining_days = 30
                        client.allowed_requests = 20000
                        client.subscribers_limit = 500
                        client.plans_limit = 8
                        client.notified_for_limit = False
                        client.notified_for_expiration = False
                        client.requests = 0
                        db.session.commit()
                        return redirect(url_for('dashboards.dashboard'))
                    except:
                        db.session.rollback()
                        flash('Failed to complete your process, please try again later.','error')
                        return redirect(url_for('dashboards.dashboard'))
                elif plan =='ultimate':
                    try:
                        if client.subscription_type == 'ultimate':
                            flash('Your ultimate plan has been renewed.','success')
                        else:
                            flash('You are now an ultimate user.','success')
                        client.subscription_type = 'ultimate'
                        client.remaining_days = 30
                        client.allowed_requests = 200000
                        client.subscribers_limit = 5000
                        client.plans_limit = 15
                        client.notified_for_limit = False
                        client.notified_for_expiration = False
                        client.requests = 0
                        db.session.commit()
                        return redirect(url_for('dashboards.dashboard'))
                    except:
                        db.session.rollback()
                        flash('Failed to complete your process, please try again later.','error')
                        return redirect(url_for('dashboards.dashboard'))
                else:
                    flash('Invalid plan name','error')
                    return redirect(url_for('main.pricing'))
            else:
                flash('Please login first','info')
                return redirect(url_for('auth.login'))
        except:
            flash('Invalid request.','error')
            return redirect(url_for('main.pricing'))

    return render_template('pricing.html', title='Subly - Pricing')

@main_bp.route('/about', methods=["GET"])
def about():
    return render_template('about.html', title='Subly - About')

@main_bp.route('/static/error_logs/', defaults={'path': ''})
@main_bp.route('/static/error_logs/<path:path>')
def block_error_logs(path):
    return abort(403)
