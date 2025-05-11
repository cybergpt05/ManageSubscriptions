from flask import Blueprint
from flask import render_template,url_for,flash,redirect,request
from ManageSubscriptions import db,limiter
from flask_login import current_user
from flask_login import login_required

developers_bp = Blueprint('developers', __name__)

@developers_bp.route('/developer/getting-started', methods=["GET"])
@login_required
def getting_started():
    return render_template('getting_started.html', title="Subly - Getting started")

@developers_bp.route('/developer/api', methods=["GET","POST"])
@login_required
def docs():
    return render_template('swagger.html')

@developers_bp.route('/developer/code-examples', methods=["GET"])
@login_required
def code_examples():
    return render_template('code_examples.html', title="Subly - Code Examples")

