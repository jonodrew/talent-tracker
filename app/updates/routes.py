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
    Promotion,
)
from app.updates import update_bp, get_candidate
from sqlalchemy import or_


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
    session["update-data"] = {}
    return render_template("search-candidate.html", error=session.pop("error", None))


@update_bp.route("/choose-update", methods=["POST", "GET"])
@get_candidate
def choose_update():
    next_steps = {
        "role": "update_bp.update_role",
        "name": "update_bp.update_name",
        "deferral": "update_bp.defer_intake",
        "email": "update_bp.new_email_address",
    }
    if request.method == "POST":
        session["update-type"] = request.form.get("update-type")
        return redirect(url_for(next_steps.get(request.form.get("update-type"))))
    return render_template("choose-update.html")


@update_bp.route("/role", methods=["POST", "GET"])
@get_candidate
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
        session["update-data"]["new-role"] = new_role
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
@get_candidate
def update_name():
    candidate_id = session.get("candidate-id")
    if not candidate_id:
        return redirect(url_for("update_bp.index"))

    if request.method == "POST":
        session["change-route"] = "update_bp.update_name"
        session["update-data"]["new-name"] = request.form.to_dict(flat=True)
        return redirect(url_for("update_bp.check_your_answers"))

    return render_template(
        "updates/name.html",
        page_header="Update name",
        candidate=Candidate.query.get(candidate_id),
    )


@update_bp.route("/deferral", methods=["POST", "GET"])
@get_candidate
def defer_intake():
    candidate_id = session.get("candidate-id")
    if not candidate_id:
        return redirect(url_for("update_bp.index"))

    if request.method == "POST":
        session["change-route"] = "update_bp.defer_intake"
        session["update-data"]["deferral"] = {
            "new-intake-year": request.form.get("new-intake-year")
        }
        return redirect(url_for("update_bp.check_your_answers"))

    return render_template(
        "updates/deferral.html",
        page_header="Defer intake year",
        candidate=Candidate.query.get(candidate_id),
    )


@update_bp.route("/email-address", methods=["POST", "GET"])
@get_candidate
def email_address():
    if request.method == "POST":
        if request.form.get("update-email-address") == "true":
            redirect_target = url_for("update_bp.new_email_address")
        else:
            redirect_target = url_for("update_bp.check_your_answers")
        return redirect(redirect_target)
    return render_template("updates/new-email-address.html")


@update_bp.route("/new-email-address", methods=["POST", "GET"])
@get_candidate
def new_email_address():
    if request.method == "POST":
        update_data = session["update-data"]
        update_data["new-email"] = {
            "which-email": request.form.get("which-email-address")
        }
        session["update-data"] = update_data
        return redirect(url_for("update_bp.update_email"))
    return render_template("updates/email-address.html")


@update_bp.route("/update-email-address", methods=["POST", "GET"])
@get_candidate
def update_email():
    if request.method == "POST":
        update_data = session["update-data"]
        update_data["new-email"]["new-address"] = request.form.get("email-address")
        session["update-data"] = update_data
        return redirect(url_for("update_bp.check_your_answers"))
    candidate = Candidate.query.get(session.get("candidate-id"))
    current_email = (
        candidate.email_address
        if session.get("which-email") == "primary-email"
        else candidate.secondary_email_address
    )
    return render_template(
        "updates/update-email-address.html",
        candidate=candidate,
        current_email=current_email,
    )


@update_bp.route("/check-your-answers", methods=["POST", "GET"])
@get_candidate
def check_your_answers():
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

    candidate = Candidate.query.get(session.get("candidate-id"))
    if request.method == "POST":
        post_your_answers()
        return redirect(url_for("update_bp.complete"))

    update_data = session.get("update-data")

    if update_data.get("new-role"):
        update_data["new-role"] = human_readable_role(update_data.get("new-role"))
    elif update_data.get("new-name"):
        update_data["name"] = {
            prettify_string(key): value
            for key, value in update_data.pop("new-name").items()
        }
    elif update_data.get("deferral"):
        update_data["deferral"] = {
            prettify_string(key): value
            for key, value in update_data.pop("deferral").items()
        }
    return render_template(
        "updates/check-your-answers.html",
        candidate=candidate,
        data=update_data,
        new_email=session.get("new-email"),
    )


def post_your_answers():
    candidate: Candidate = Candidate.query.get(session.get("candidate-id"))
    update_data = session.get("update-data")

    def new_email_address():
        email_data = update_data.get("new-email")
        primary = True if email_data.get("which-email") == "primary-email" else False
        candidate.update_email(email_data.get("new-address"), primary)

    if update_data.get("new-role"):
        role_data = update_data.get("new-role")
        candidate.new_role(
            start_date=date(
                role_data["start-date-year"],
                role_data["start-date-month"],
                role_data["start-date-day"],
            ),
            new_org_id=role_data["new-org"],
            new_profession_id=role_data["new-profession"],
            new_location_id=role_data["new-location"],
            new_grade_id=role_data["new-grade"],
            new_title=role_data["new-title"],
            role_change_id=role_data["role-change"],
        )
    elif update_data.get("new-name"):
        name_data = update_data.get("new-name")
        candidate.first_name = name_data.get("first-name")
        candidate.last_name = name_data.get("last-name")
    elif update_data.get("new-intake-year"):
        new_scheme_start_date = date(int(session.pop("new-intake-year")), 3, 1)
        candidate.applications[0].defer(new_scheme_start_date)
    elif update_data.get("deferral"):
        candidate.applications.first().defer(
            date(int(update_data["deferral"].get("new-intake-year")), 3, 1)
        )

    if update_data.get("new-email"):
        new_email_address()

    db.session.add(candidate)
    db.session.commit()


@update_bp.route("/complete", methods=["GET"])
@get_candidate
def complete():
    return render_template("updates/complete.html")
