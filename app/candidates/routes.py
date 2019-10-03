from app.models import *
from app.candidates import candidates_bp
from flask import render_template, abort


@candidates_bp.route("/<int:candidate_id>", methods=["POST", "GET"])
def candidate_profile(candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return abort(404)
    return render_template("candidates/profile.html", candidate=candidate)
