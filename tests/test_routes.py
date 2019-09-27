import pytest
from flask import url_for, session

from app.models import (
    Grade,
    Organisation,
    Profession,
    Location,
    Role,
    AuditEvent,
    Promotion,
)
from flask_login import current_user


def test_home_status_code(test_client, logged_in_user):
    # sends HTTP GET request to the application
    # on the specified path
    result = test_client.get("/")

    # assert the status code of the response
    assert result.status_code == 200


class TestNewEmail:
    def test_get(self, test_client, logged_in_user):
        result = test_client.get("/update/email-address")
        assert b"Has the candidate got a new email address?" in result.data

    def test_post(self, test_client, logged_in_user, test_candidate):

        with test_client.session_transaction() as sess:
            sess["candidate-id"] = 1
        data = {
            "update-email-address": "true",
            "new-email-address": "new-test-email@gov.uk",
        }
        test_client.post("/update/email-address", data=data)
        assert "new-test-email@gov.uk" == session.get("new-email")


class TestUpdateType:
    @pytest.mark.parametrize("option", ["Role", "Name", "Deferral"])
    def test_get(self, option, test_client, logged_in_user):
        result = test_client.get(url_for("route_blueprint.choose_update"))
        assert option in result.data.decode("UTF-8")


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
        test_client.post("/update/role", data=data)
        assert data.keys() == session.get("new-role").keys()


class TestSearchCandidate:
    def test_get(self, test_client, logged_in_user):
        result = test_client.get("/update/search-candidate")
        assert "Most recent candidate email address" in result.data.decode("UTF-8")

    @pytest.mark.parametrize(
        "email",
        ("test.candidate@numberten.gov.uk", "test.secondary@gov.uk")
    )
    @pytest.mark.parametrize(
        "update_type, expected_title",
        [
            ("role", "Role update"),
            ("name", "Update name"),
            ("deferral", "Defer intake year"),
        ],
    )
    def test_post(
        self,
        update_type,
        expected_title,
        test_client,
        test_candidate,
        logged_in_user,
        test_roles,
        email
    ):
        with test_client.session_transaction() as sess:
            sess["update-type"] = update_type
        data = {"candidate-email": email}
        result = test_client.post(
            "/update/search-candidate",
            data=data,
            follow_redirects=True,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )

        assert expected_title in result.data.decode("UTF-8")

        assert 1 == session.get("candidate-id")

    def test_given_candidate_email_doesnt_exist_when_user_searches_then_user_is_redirected_to_new_search(
        self, test_client, logged_in_user
    ):
        with test_client.session_transaction() as sess:
            sess["update-type"] = "role"
        data = {"candidate-email": "no-such-candidate@numberten.gov.uk"}
        result = test_client.post(
            "/update/search-candidate",
            data=data,
            follow_redirects=False,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert result.status_code == 302
        assert (
            result.location
            == f"http://localhost{url_for('route_blueprint.search_candidate')}"
        )


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
    role_change = Promotion.query.first()
    with test_client.session_transaction() as sess:
        sess["new-role"] = {
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
        sess["data-update"] = dict()
        sess["candidate-id"] = test_candidate.id
    test_client.post("/update/check-your-answers")
    latest_role: Role = test_candidate.roles.order_by(Role.id.desc()).first()
    assert "Organisation 1" == Organisation.query.get(latest_role.organisation_id).name
    assert "Senior dev" == latest_role.role_name
    assert "substantive promotion" == latest_role.role_change.value


class TestAuthentication:
    def test_login(self, logged_in_user):
        assert current_user.is_authenticated

    @pytest.mark.parametrize(
        "url",
        [
            "/update/search-candidate",
            "/reports/",
            "/update/search-candidate",
            "/candidates/candidate/1",
        ],
    )
    def test_non_logged_in_users_are_redirected_to_login(self, url, test_client):
        with test_client:
            response = test_client.get(url, follow_redirects=False)
        assert response.status_code == 302  # 302 is the redirect code
        assert response.location == url_for("auth_bp.login", _external=True)


class TestReports:
    def test_get(self, test_client, logged_in_user):
        result = test_client.get("/reports/")
        assert "Select report" in result.data.decode("utf-8")

    def test_post(self, test_client, logged_in_user):
        data = {
            "report-type": "promotions",
            "scheme": "FLS",
            "year": 2018,
            "attribute": "ethnicity",
        }
        result = test_client.post("/reports/", data=data)
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
        result = test_client.get("/candidates/candidate/1")
        assert "Career profile for Testy Candidate" in result.data.decode("utf-8")


def test_audit_events(test_client, logged_in_user):
    data = {
        "report-type": "promotions",
        "scheme": "FLS",
        "year": 2018,
        "attribute": "ethnicity",
    }
    test_client.post("/reports/", data=data)
    events: AuditEvent = AuditEvent.query.first()
    assert (
        "Generated a promotions report on ethnicity for FLS 2018 intake"
        == events.action_taken
    )
