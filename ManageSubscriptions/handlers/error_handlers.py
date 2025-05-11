from flask import Blueprint
from flask import url_for,flash,redirect,request
from flask_limiter.errors import RateLimitExceeded

handlers_bp = Blueprint('handlers', __name__)


@handlers_bp.errorhandler(RateLimitExceeded)
def handle_ratelimit_error(e):
    endpoint = request.endpoint

    if endpoint == 'login':
        flash("You exceeded login attempts, Please wait before trying again.", "error")
        return redirect(url_for("auth.login"))
    elif request.path.startswith('/confirm/'):
        flash("You exceeded confirmation attempts, Please wait before trying again.", "error")
        return redirect(url_for("auth.login"))
    elif endpoint == 'request_reset':
        flash("Please wait 15 minutes before requesting a new reset email.", "info")
        return redirect(url_for("auth.request_reset"))
    elif endpoint == 'reset_password':
        flash("You exceeded changing password attempts limit for this token, please request a new one.", "error")
        return redirect(url_for("auth.reset_password"))
    elif endpoint == 'support':
        flash("You exceeded your limit for sending masseges, please wait for an hour to be able to send again.", "error")
        return redirect(url_for("forms.support"))
    else:
        flash("You exceeded your limit.", "error")
        return redirect(url_for("main.index"))

@handlers_bp.errorhandler(413)
def handle_too_large(e):
    flash('File is too large, The maximum allowed is 5MB', 'error')
    return redirect(url_for('dashboards.my_account'))