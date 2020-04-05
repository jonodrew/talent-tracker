import pytest
from flask import url_for, session
from datetime import date

from app.models import (
    Grade,
    Organisation,
    Profession,
    Location,
    Role,
    AuditEvent,
    Promotion,
    RoleChangeEvent,
)
from flask_login import current_user


def test_home_status_code(test_client, logged_in_user):
    # sends HTTP GET request to the application
    # on the specified path
    result = test_client.get("/")

    # assert the status code of the response
    assert result.status_code == 200


class TestNewEmail:
    def test_get(self, test_client, logged_in_user, candidate_in_session):
        result = test_client.get(url_for("update_bp.email_address"))
        assert b"Has the candidate got a new email address?" in result.data

    def test_post_new_address(self, test_client, logged_in_user, test_candidate):

        with test_client.session_transaction() as sess:
            sess["candidate-id"] = 1
        data = {"update-email-address": "true"}
        result = test_client.post(
            url_for("update_bp.email_address"), data=data, follow_redirects=True
        )
        assert (
            "Which of the candidate's email addresses do you want to change?"
            in result.data.decode("UTF-8")
        )

    def test_post_no_new_address(self, test_client, logged_in_user):
        with test_client.session_transaction() as sess:
            sess["candidate-id"] = 1
        data = {"update-email-address": "false"}
        result = test_client.post(
            "/update/email-address",
            data=data,
            follow_redirects=False,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert (
            result.location
            == f"http://localhost{url_for('update_bp.check_your_answers')}"
        )


class TestUpdateType:
    @pytest.mark.parametrize("option", ["Role", "Name", "Deferral", "Email"])
    def test_get(self, option, test_client, logged_in_user, candidate_in_session):
        result = test_client.get(url_for("update_bp.choose_update"))
        assert option in result.data.decode("UTF-8")

    @pytest.mark.parametrize(
        "option, destination",
        [
            ("email", "new_email_address"),
            ("role", "update_role"),
            ("name", "update_name"),
            ("deferral", "defer_intake"),
        ],
    )
    def test_post_returns_correct_destination(
        self,
        option,
        destination,
        test_client,
        logged_in_user,
        test_session,
        candidate_in_session,
    ):
        destination_url = url_for(f"update_bp.{destination}")
        result = test_client.post(
            url_for("update_bp.choose_update"),
            data={"update-type": option},
            follow_redirects=False,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert result.location == f"http://localhost{destination_url}"


class TestRoleUpdate:
    def test_get(self, test_client, test_candidate, logged_in_user, test_roles):
        with test_client.session_transaction() as sess:
            sess["candidate-id"] = 1
        result = test_client.get(f"/update/role", follow_redirects=False)
        assert f'<h1 class="govuk-heading-xl">Role update</h1>' in result.data.decode(
            "UTF-8"
        )

    def test_post(self, test_client, test_candidate, test_session, logged_in_user):
        higher_grade = Grade.query.filter(Grade.value == "SCS3").first()
        test_session.bulk_save_objects(
            [
                Organisation(name="Number 11", department=False),
                Profession(value="Digital, Data and Technology"),
                Location(value="London"),
            ]
        )
        test_session.commit()
        new_org = Organisation.query.first()
        new_profession = Profession.query.first()
        new_location = Location.query.first()
        data = {
            "new-grade": higher_grade.id,
            "start-date-day": "1",
            "start-date-month": "1",
            "start-date-year": "2019",
            "new-org": str(new_org.id),
            "new-profession": str(new_profession.id),
            "new-location": str(new_location.id),
            "role-change": "1",
            "new-title": "Senior dev",
        }
        with test_client.session_transaction() as sess:
            sess["update-data"] = {}
            sess["candidate-id"] = test_candidate.id
        test_client.post("/update/role", data=data, follow_redirects=False)
        assert data.keys() == session.get("update-data").get("new-role").keys()


class TestSearchCandidate:
    def test_get(self, test_client, logged_in_user, candidate_in_session):
        result = test_client.get(url_for("update_bp.index"))
        assert "Most recent candidate email address" in result.data.decode("UTF-8")

    @pytest.mark.parametrize(
        "email", ("test.candidate@numberten.gov.uk", "test.secondary@gov.uk")
    )
    def test_post(
        self,
        candidate_in_session,
        test_client,
        test_candidate,
        logged_in_user,
        test_roles,
        email,
    ):
        data = {"candidate-email": email}
        test_client.post(
            "/update/",
            data=data,
            follow_redirects=True,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )

        assert 1 == session.get("candidate-id")

    def test_given_candidate_email_doesnt_exist_when_user_searches_then_user_is_redirected_to_new_search(
        self, test_client, logged_in_user, candidate_in_session
    ):
        data = {"candidate-email": "no-such-candidate@numberten.gov.uk"}
        result = test_client.post(
            url_for("update_bp.index"),
            data=data,
            follow_redirects=False,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert result.status_code == 302
        assert result.location == f"http://localhost{url_for('update_bp.index')}"


def test_check_details(
    logged_in_user,
    test_client,
    test_session,
    test_candidate,
    test_locations,
    test_orgs,
    test_professions,
):
    higher_grade = Grade.query.filter(Grade.value == "SCS3").first()
    new_org = Organisation.query.first()
    new_profession = Profession.query.first()
    new_location = Location.query.first()
    role_change = Promotion.query.filter_by(value="substantive").first()
    with test_client.session_transaction() as sess:
        sess["update-data"] = {}
        sess["update-data"]["new-role"] = {
            "new-grade": higher_grade.id,
            "start-date-day": 1,
            "start-date-month": 1,
            "start-date-year": 2019,
            "new-org": new_org.id,
            "new-profession": new_profession.id,
            "role-change": role_change.id,
            "new-location": new_location.id,
            "new-title": "Senior dev",
        }
        sess["update-data"]["new-email"] = {
            "new-address": "changed_address@gov.uk",
            "which-email": "primary-email",
        }
        sess["candidate-id"] = test_candidate.id
    test_client.post("/update/check-your-answers")
    latest_role: Role = test_candidate.roles.order_by(Role.id.desc()).first()
    assert "Organisation 1" == Organisation.query.get(latest_role.organisation_id).name
    assert "Senior dev" == latest_role.role_name
    assert "substantive" == latest_role.role_change.value
    assert "changed_address@gov.uk" == test_candidate.email_address

    assert len(RoleChangeEvent.query.all()) == 1
    role_change_event: RoleChangeEvent = RoleChangeEvent.query.first()
    assert role_change_event.new_role_id == latest_role.id
    assert role_change_event.role_change_date == date(2019, 1, 1)


class TestAuthentication:
    def test_login(self, logged_in_user):
        assert current_user.is_authenticated

    @pytest.mark.parametrize("url", ["/update/", "/reports/", "/candidates/1"])
    def test_non_logged_in_users_are_redirected_to_login(self, url, test_client):
        with test_client:
            response = test_client.get(url, follow_redirects=False)
        assert response.status_code == 302  # 302 is the redirect code
        assert response.location == url_for("auth_bp.login", _external=True)


class TestReports:
    def test_get_promotions(self, test_client, logged_in_user):
        result = test_client.get("/reports/promotions")
        assert "Promotion report" in result.data.decode("utf-8")

    def test_post_promotions(self, test_client, logged_in_user):
        data = {
            "report-type": "promotions",
            "scheme": "FLS",
            "year": 2018,
            "attribute": "ethnicity",
        }
        result = test_client.post("/reports/promotions", data=data)
        assert 200 == result.status_code

    def test_get_detailed_report(self, test_client, logged_in_user):
        result = test_client.get("/reports/detailed")
        assert "Detailed Report" in result.data.decode("utf-8")

    def test_post_detailed_report(self, test_client, logged_in_user):
        data = {"scheme": "FLS", "year": "2018", "promotion-type": 1}
        result = test_client.post("/reports/detailed", data=data)
        assert 200 == result.status_code


class TestProfile:
    def test_get(self, test_client, logged_in_user, test_candidate_applied_to_fls):
        result = test_client.get("/candidates/1")
        assert "Career profile for Testy Candidate" in result.data.decode("utf-8")


def test_audit_events(test_client, logged_in_user):
    data = {
        "report-type": "promotions",
        "scheme": "FLS",
        "year": 2018,
        "attribute": "ethnicity",
    }
    test_client.post("/reports/promotions", data=data)
    events: AuditEvent = AuditEvent.query.first()
    assert (
        "Generated a promotions report on ethnicity for FLS 2018 intake"
        == events.action_taken
    )
