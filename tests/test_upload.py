from app.models import Candidate
import modules.seed as sd
import pytest
from datetime import date


@pytest.mark.parametrize("scheme", ["FLS"])
@pytest.mark.parametrize("year", ["2019"])
class TestUpload:
    def test_create_candidate_data(
        self, year, scheme, test_upload_object, detailed_candidate, test_session
    ):
        sd.clear_old_data()
        sd.commit_data()
        u = test_upload_object(
            f"tests/data/{year}/test_csv.csv",
            f"tests/data/{year}/test_application_csv.csv",
            False,
            scheme,
        )
        u.complete_upload()
        candidate = Candidate.query.filter_by(first_name="James").first()
        assert candidate
        assert len(candidate.applications.all()) == 1
        assert len(candidate.roles.all()) == 2
        assert candidate.sexuality_id == 0
        assert candidate.current_grade().value == "Grade 6"
        assert candidate.roles[0].date_started == date(2019, 1, 1)

    @pytest.mark.parametrize(
        "csv_field, db_field, new_data",
        [
            ("Forename", "first_name", "[REDACTED - FIRST NAME]"),
            ("Surname_x", "last_name", "[REDACTED - LAST NAME]"),
        ],
    )
    def test_redact_replaces_personal_data_with_redacted(
        self, year, scheme, csv_field, db_field, new_data, test_upload_object
    ):
        sd.clear_old_data()
        sd.commit_data()
        u = test_upload_object(
            f"tests/data/{year}/test_csv.csv",
            f"tests/data/{year}/test_application_csv.csv",
            True,
            scheme,
        )
        u.complete_upload()
        candidate = Candidate.query.filter_by(email_address="PU007@gov.uk").first()
        assert candidate.__getattribute__(db_field) == new_data

    def test_redact_mixes_up_protected_characteristics(
        self, year, scheme, test_session, detailed_candidate, test_upload_object
    ):
        u = test_upload_object(
            f"tests/data/{year}/test_csv.csv",
            f"tests/data/{year}/test_application_csv.csv",
            True,
            scheme,
        )
        u.complete_upload()
        candidate = Candidate.query.filter_by(email_address="PU007@gov.uk").first()
        assert candidate.sexuality.value == "Pan"
        assert candidate.belief.value == "Don't forget to be awesome"
        assert candidate.ethnicity.value == "Terran"
        assert candidate.gender.value in ["Fork", "Knife", "Chopsticks"]
        assert candidate.main_job_type.value == "Roboticist"
