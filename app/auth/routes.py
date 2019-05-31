from flask import render_template, request, url_for, redirect
from app.models import User
from flask_login import login_user, logout_user
from flask import flash
from app.auth import auth_blueprint


@auth_blueprint.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get('email-address')).first()
        if user is None or not user.check_password(request.form.get('password')):
            return redirect(url_for('auth.login'))
        login_user(user)

        flash('Logged in successfully.')

        next = request.args.get('next')

        return redirect(next or url_for('route_blueprint.choose_update'))
    return render_template('login.html')


@auth_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('.login'))