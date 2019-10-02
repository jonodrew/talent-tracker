from flask import Blueprint, redirect, url_for
from flask_login import current_user

update_bp = Blueprint("update_bp", __name__)


@update_bp.before_request
def restrict_to_logged_in_users():
    if not current_user.is_authenticated:
        return redirect(url_for("auth_bp.login"))


from app.updates import routes  # noqa: E402,F401
