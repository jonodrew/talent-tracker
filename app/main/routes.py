from app.main import main_bp
from flask import render_template


@main_bp.route("/")
def hello_world():
    return render_template("index.html")


@main_bp.route("/hello")
def hello():
    return "Hello world"
