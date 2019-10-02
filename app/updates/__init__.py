from flask import Blueprint, redirect, url_for, session
from flask_login import current_user
from app.models import Candidate

update_bp = Blueprint("update_bp", __name__)


@update_bp.before_request
def restrict_to_logged_in_users():
    if not current_user.is_authenticated:
        return redirect(url_for("auth_bp.login"))


@update_bp.before_request
def get_candidate():
    if not session.get("candidate"):
        candidate = Candidate.query.get(session.get("candidate-id"))
        session["candidate"] = {
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
        }


from app.updates import routes  # noqa: E402,F401
