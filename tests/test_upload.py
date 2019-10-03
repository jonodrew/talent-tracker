from modules.upload import Upload
import os
from app.models import Candidate, Organisation
import modules.seed as sd
import pytest
from datetime import date


class TestUpload:
    def test_create_candidate_data(self, test_session):
        sd.clear_old_data()
        sd.commit_data()
        test_session.add(Organisation(name="Foreign and Commonwealth Office"))
        test_session.commit()
        directory = os.path.dirname(__file__)
        intake_filename = os.path.join(directory, "data/test_csv.csv")
        application_filename = os.path.join(directory, "data/test_application_csv.csv")
        u = Upload(intake_filename, "FLS", "2020-3-3", application_filename)
        u.complete_upload()
        candidate = Candidate.query.filter_by(first_name="James").first()
        assert candidate
        assert len(candidate.applications.all()) == 1
        assert len(candidate.roles.all()) == 2
        assert candidate.sexuality_id == 0
        assert candidate.current_grade().value == "Grade 6"
        assert candidate.roles[0].date_started == date(2019, 1, 1)
        assert (
            candidate.most_recent_application().aspirational_grade.value
            == "SCS2 - Director"
        )

    @pytest.mark.parametrize(
        "csv_field, db_field, new_data",
        [
            ("Forename", "first_name", "[REDACTED - FIRST NAME]"),
            ("Surname_x", "last_name", "[REDACTED - LAST NAME]"),
        ],
    )
    @pytest.mark.parametrize("year", ["2019"])
    def test_redact_replaces_personal_data_with_redacted(
        self, year, csv_field, db_field, new_data, test_upload_object
    ):
        sd.clear_old_data()
        sd.commit_data()
        u = test_upload_object(
            f"tests/data/{year}/test_csv.csv",
            f"tests/data/{year}/test_application_csv.csv",
            True,
        )
        u.complete_upload()
        candidate = Candidate.query.filter_by(email_address="PU007@gov.uk").first()
        assert candidate.__getattribute__(db_field) == new_data

    @pytest.mark.parametrize("year", ["2019"])
    def test_redact_mixes_up_protected_characteristics(
        self, year, test_session, detailed_candidate, test_upload_object
    ):
        u = test_upload_object(
            f"tests/data/{year}/test_csv.csv",
            f"tests/data/{year}/test_application_csv.csv",
            True,
        )
        u.complete_upload()
        candidate = Candidate.query.filter_by(email_address="PU007@gov.uk").first()
        assert candidate.sexuality.value == "Pan"
        assert candidate.belief.value == "Don't forget to be awesome"
        assert candidate.ethnicity.value == "Terran"
        assert candidate.gender.value in ["Fork", "Knife", "Chopsticks"]
        assert candidate.main_job_type.value == "Roboticist"
