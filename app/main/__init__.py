from flask import Blueprint

main_bp = Blueprint("main_bp", __name__)


from app.main import routes  # noqa: E402,F401
