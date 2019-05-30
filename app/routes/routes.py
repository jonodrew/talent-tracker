from flask import render_template, request, url_for, redirect, session
from app.models import Candidate, Grade, db, Role, Organisation, Location, Profession, User
from app.routes import route_blueprint
from flask_login import login_user
from datetime import date
from flask import flash


@route_blueprint.route('/login', methods=["POST", "GET"])
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



@route_blueprint.route('/')
def hello_world():
    return render_template('index.html')


@route_blueprint.route('/hello')
def hello():
    return 'Hello world'


@route_blueprint.route('/results')
def results():
    candidates = Candidate.query.all()
    return render_template('results.html', candidates=candidates, heading='Search results', accordion_data=[
        {'heading': 'Heading', 'content': 'Lorem ipsum, blah blah'}
    ])


@route_blueprint.route('/update', methods=["POST", "GET"])
def choose_update():
    next_steps = {
        'role': 'route_blueprint.search_candidate'
    }
    if request.method == "POST":
        session['bulk-single'] = request.form.get("bulk-single")
        session['update-type'] = request.form.get("update-type")
        return redirect(url_for(next_steps.get(request.form.get("update-type"))))
    return render_template('choose-update.html')


@route_blueprint.route('/update/search-candidate', methods=["POST", "GET"])
def search_candidate():
    if request.method == "POST":
        session['candidate-email'] = request.form.get('candidate-email')
        return redirect(url_for('route_blueprint.update', bulk_or_single=session.get('bulk-single'),
                                update_type=session.get('update-type')))
    return render_template('search-candidate.html')


@route_blueprint.route('/update/<string:bulk_or_single>/<string:update_type>', methods=["POST", "GET"])
def update(bulk_or_single, update_type):
    candidate = Candidate.query.filter_by(personal_email=session.get('candidate-email')).one_or_none()
    if request.method == 'POST':
        form_dict = {k: int(v[0]) for k, v in request.form.to_dict(flat=False).items()}
        db.session.add(Role(
            date_started=date(
                year=form_dict.get('start-date-year'), month=form_dict.get('start-date-month'),
                day=form_dict.get('start-date-day')
            ),
            organisation_id=form_dict.get('new-org'), candidate_id=candidate.id,
            profession_id=form_dict.get('new-profession'), location_id=form_dict.get('new-location'),
            grade_id=form_dict.get('new-grade')
        ))
        db.session.commit()
        return redirect(url_for('route_blueprint.complete'))
    # TODO: if candidate doesn't exist, return user to search page
    update_types = {
        "role": {'title': "Role update", "promotable_grades": Grade.promotion_roles(Grade(value='Grade name', rank=7)),
                 "organisations": Organisation.query.all(), "locations": Location.query.all(),
                 "professions": Profession.query.all()
                 },
        "fls-survey": "FLS Survey update", "sls-survey": "SLS Survey update"
    }
    template = f"updates/{bulk_or_single}-{update_type}.html"
    return render_template(template, page_header=update_types.get(update_type).get('title'),
                           data=update_types.get(update_type), candidate=candidate)


@route_blueprint.route('/update/complete', methods=["GET"])
def complete():
    return render_template('updates/complete.html')
