from datetime import date
from typing import Dict

from flask import render_template, request, url_for, redirect, session
from app.models import Candidate, Grade, db, Organisation, Location, Profession, Role
from app.routes import route_blueprint


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
        'role': 'route_blueprint.search_candidate',
        'name': 'route_blueprint.update_name'
    }
    if request.method == "POST":
        session['bulk-single'] = request.form.get("bulk-single")
        session['update-type'] = request.form.get("update-type")
        return redirect(url_for(next_steps.get(request.form.get("update-type"))))
    return render_template('choose-update.html')


@route_blueprint.route('/update/search-candidate', methods=["POST", "GET"])
def search_candidate():
    if request.method == "POST":
        candidate = Candidate.query.filter_by(email_address=request.form.get('candidate-email')).one_or_none()
        if candidate:
            session['candidate-id'] = candidate.id
        else:
            session['error'] = "That email does not exist"
            return redirect(url_for('route_blueprint.search_candidate'))
        return redirect(url_for('route_blueprint.update', bulk_or_single=session.get('bulk-single'),
                                update_type=session.get('update-type')))
    return render_template('search-candidate.html', error=session.pop('error', None))


@route_blueprint.route('/update/<string:bulk_or_single>/<string:update_type>', methods=["POST", "GET"])
def update(bulk_or_single, update_type):
    candidate_id = session.get('candidate-id')
    if not candidate_id:
        return redirect(url_for('route_blueprint.search_candidate'))

    if request.method == 'POST':
        session['new-role'] = {key: int(value[0]) for key, value in request.form.to_dict(flat=False).items()}
        return redirect(url_for('route_blueprint.email_address'))

    update_types = {
        "role": {'title': "Role update",
                 "promotable_grades": Grade.new_grades(Candidate.query.get(candidate_id).current_grade()),
                 "organisations": Organisation.query.all(), "locations": Location.query.all(),
                 "professions": Profession.query.all()
                 },
        "fls-survey": "FLS Survey update", "sls-survey": "SLS Survey update"
    }
    template = f"updates/{bulk_or_single}-{update_type}.html"
    return render_template(template, page_header=update_types.get(update_type).get('title'),
                           data=update_types.get(update_type), candidate=Candidate.query.get(candidate_id))


@route_blueprint.route('/update/name', methods=["POST", "GET"])
def update_name():
    candidate_id = session.get('candidate-id')
    if not candidate_id:
        return redirect(url_for('route_blueprint.search_candidate'))

    if request.method == "POST":
        session['new-name'] = request.form.to_dict(flat=True)
        return redirect(url_for('route_blueprint.check_your_answers'))

    return render_template('updates/name.html', page_header='Update name',
                           candidate=Candidate.query.get(candidate_id))


@route_blueprint.route('/update/email-address', methods=["POST", "GET"])
def email_address():
    if request.method == "POST":
        if request.form.get("update-email-address") == "true":
            session['new-email'] = request.form.get("new-email-address")

        return redirect(url_for('route_blueprint.check_your_answers'))

    return render_template('updates/email-address.html')


@route_blueprint.route('/update/check-your-answers', methods=["POST", "GET"])
def check_your_answers():
    candidate = Candidate.query.get(session.get('candidate-id'))
    if request.method == "POST":
        if session.get('new-role'):
            role_data = session.pop('new-role', None)
            session.pop('data-update')
            candidate.roles.append(Role(
                date_started=date(role_data['start-date-year'], role_data['start-date-month'],
                                  role_data['start-date-day']),
                temporary_promotion=bool(role_data['temporary-promotion']), organisation_id=role_data['new-org'],
                profession_id=role_data['new-profession'], location_id=role_data['new-location'],
                grade_id=role_data['new-grade']
            ))
            new_email = session.get('new-email')
            if new_email:
                candidate.email_address = new_email
        elif session.get('new-name'):
            name_data = session.pop('new-name')
            candidate.first_name = name_data.get('first-name')
            candidate.last_name = name_data.get('last-name')

        db.session.add(candidate)
        db.session.commit()

        return redirect(url_for('route_blueprint.complete'))

    def prettify_string(string_to_prettify):
        string_as_list = list(string_to_prettify)
        string_as_list[0] = string_as_list[0].upper()
        string_as_list = [letter if letter != "-" else " " for letter in string_as_list]
        return ''.join(string_as_list)

    def human_readable_role(role_data: Dict):
        data = role_data.copy()
        data['start-date'] = date(data['start-date-year'], data['start-date-month'], data['start-date-day'])
        data.pop('start-date-day')
        data.pop('start-date-month')
        data.pop('start-date-year')
        data = {prettify_string(key): value for key, value in data.items()}
        data['New grade'] = Grade.query.get(data['New grade']).value
        data['New location'] = Location.query.get(data['New location']).value
        data['New org'] = Organisation.query.get(data['New org']).name
        data['New profession'] = Profession.query.get(data['New profession']).value
        data['Temporary promotion'] = "Yes" if bool(data['Temporary promotion']) else "No"

        return data
    if session.get('new-role'):
        session['data-update'] = human_readable_role(session['new-role'])
    elif session.get('new-name'):
        session['data-update'] = {prettify_string(key): value for key, value in session.get('new-name').items()}
    return render_template('updates/check-your-answers.html',
                           candidate=candidate, data=session.get('data-update'), new_email=session.get('new-email'))


@route_blueprint.route('/update/complete', methods=["GET"])
def complete():
    return render_template('updates/complete.html')
