from datetime import date
from typing import Dict

from flask import render_template, request, url_for, redirect, session
from app.models import (
    Candidate,
    Grade,
    db,
    Organisation,
    Location,
    Profession,
    Role,
    Promotion,
)
from app.updates import update_bp
from sqlalchemy import or_


@update_bp.route("/results")
def results():
    candidates = Candidate.query.all()
    return render_template(
        "results.html",
        candidates=candidates,
        heading="Search results",
        accordion_data=[{"heading": "Heading", "content": "Lorem ipsum, blah blah"}],
    )


@update_bp.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        email = request.form.get("candidate-email")
        candidate = Candidate.query.filter(
            or_(
                Candidate.email_address == email,
                Candidate.secondary_email_address == email,
            )
        ).first()
        if candidate:
            session["candidate-id"] = candidate.id
        else:
            session["error"] = "That email does not exist"
            return redirect(url_for("update_bp.index"))
        return redirect(url_for("update_bp.choose_update"))
    return render_template("search-candidate.html", error=session.pop("error", None))


@update_bp.route("/choose-update", methods=["POST", "GET"])
def choose_update():
    next_steps = {
        "role": "update_bp.update_role",
        "name": "update_bp.update_name",
        "deferral": "update_bp.defer_intake",
        "email": "update_bp.new_email_address"
    }
    if request.method == "POST":
        session["update-type"] = request.form.get("update-type")
        return redirect(url_for(next_steps.get(request.form.get("update-type"))))
    return render_template("choose-update.html")


@update_bp.route("/role", methods=["POST", "GET"])
def update_role():
    candidate_id = session.get("candidate-id")
    if not candidate_id:
        return redirect(url_for("update_bp.index"))

    if request.method == "POST":
        session["change-route"] = "update_bp.update_role"
        form_as_dict: dict = request.form.to_dict(flat=False)
        new_role_title = {"new-title": form_as_dict.pop("new-title")[0]}
        new_role_numbers = {key: int(value[0]) for key, value in form_as_dict.items()}
        new_role = {**new_role_numbers, **new_role_title}
        session["new-role"] = new_role
        return redirect(url_for("update_bp.email_address"))

    data = {
        "promotable_grades": Grade.new_grades(
            Candidate.query.get(candidate_id).current_grade()
        ),
        "organisations": Organisation.query.all(),
        "locations": Location.query.all(),
        "professions": Profession.query.all(),
        "role_changes": Promotion.query.all(),
    }
    return render_template(
        "updates/role.html",
        page_header="Role update",
        data=data,
        candidate=Candidate.query.get(candidate_id),
    )


@update_bp.route("/name", methods=["POST", "GET"])
def update_name():
    candidate_id = session.get("candidate-id")
    if not candidate_id:
        return redirect(url_for("update_bp.index"))

    if request.method == "POST":
        session["change-route"] = "update_bp.update_name"
        session["new-name"] = request.form.to_dict(flat=True)
        return redirect(url_for("update_bp.check_your_answers"))

    return render_template(
        "updates/name.html",
        page_header="Update name",
        candidate=Candidate.query.get(candidate_id),
    )


@update_bp.route("/deferral", methods=["POST", "GET"])
def defer_intake():
    candidate_id = session.get("candidate-id")
    if not candidate_id:
        return redirect(url_for("update_bp.index"))

    if request.method == "POST":
        session["change-route"] = "update_bp.defer_intake"
        session["new-intake-year"] = request.form.get("new-intake-year")
        return redirect(url_for("update_bp.check_your_answers"))

    return render_template(
        "updates/deferral.html",
        page_header="Defer intake year",
        candidate=Candidate.query.get(candidate_id),
    )


@update_bp.route("/email-address", methods=["POST", "GET"])
def email_address():
    if request.method == "POST":
        if request.form.get("update-email-address") == "true":
            redirect_target = url_for("update_bp.new_email_address")
        else:
            redirect_target = url_for("update_bp.check_your_answers")
        return redirect(redirect_target)

    return render_template("updates/new-email-address.html")


@update_bp.route("/new-email-address", methods=["POST", "GET"])
def new_email_address():
    return render_template("updates/email-address.html")


@update_bp.route("/check-your-answers", methods=["POST", "GET"])
def check_your_answers():
    candidate = Candidate.query.get(session.get("candidate-id"))
    if request.method == "POST":
        session.pop("data-update")
        if session.get("new-role"):
            role_data = session.pop("new-role", None)
            candidate.roles.append(
                Role(
                    date_started=date(
                        role_data["start-date-year"],
                        role_data["start-date-month"],
                        role_data["start-date-day"],
                    ),
                    organisation_id=role_data["new-org"],
                    profession_id=role_data["new-profession"],
                    location_id=role_data["new-location"],
                    grade_id=role_data["new-grade"],
                    role_name=role_data["new-title"],
                    role_change_id=role_data["role-change"],
                )
            )
            new_email = session.get("new-email")
            if new_email:
                candidate.email_address = new_email
        elif session.get("new-name"):
            name_data = session.pop("new-name")
            candidate.first_name = name_data.get("first-name")
            candidate.last_name = name_data.get("last-name")
        elif session.get("new-intake-year"):
            new_scheme_start_date = date(int(session.pop("new-intake-year")), 3, 1)
            candidate.applications[0].defer(new_scheme_start_date)

        db.session.add(candidate)
        db.session.commit()

        return redirect(url_for("update_bp.complete"))

    def prettify_string(string_to_prettify):
        string_as_list = list(string_to_prettify)
        string_as_list[0] = string_as_list[0].upper()
        string_as_list = [letter if letter != "-" else " " for letter in string_as_list]
        return "".join(string_as_list)

    def human_readable_role(role_data: Dict):
        data = role_data.copy()
        data["start-date"] = date(
            data["start-date-year"], data["start-date-month"], data["start-date-day"]
        )
        data.pop("start-date-day")
        data.pop("start-date-month")
        data.pop("start-date-year")
        role_id = data.pop("role-change")
        data = {prettify_string(key): value for key, value in data.items()}
        data["New grade"] = Grade.query.get(data["New grade"]).value
        data["New location"] = Location.query.get(data["New location"]).value
        data["New org"] = Organisation.query.get(data["New org"]).name
        data["New profession"] = Profession.query.get(data["New profession"]).value
        data["Role change type"] = Promotion.query.get(role_id).value

        return data

    if session.get("new-role"):
        session["data-update"] = human_readable_role(session["new-role"])
    elif session.get("new-name"):
        session["data-update"] = {
            prettify_string(key): value
            for key, value in session.get("new-name").items()
        }
    elif session.get("new-intake-year"):
        session["data-update"] = {"New intake year": session.get("new-intake-year")}
    return render_template(
        "updates/check-your-answers.html",
        candidate=candidate,
        data=session.get("data-update"),
        new_email=session.get("new-email"),
    )


@update_bp.route("/complete", methods=["GET"])
def complete():
    return render_template("updates/complete.html")


@update_bp.route("/candidate")
def candidate():
    return render_template(
        "candidates/profile.html",
        roles=Role.query.order_by(Role.date_started.desc()).all(),
        candidate=Candidate.query.get(2),
    )
