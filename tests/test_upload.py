from app.models import (
    Candidate,
    Organisation,
    Belief,
    Sexuality,
    Ethnicity,
    Gender,
)
import pytest
from datetime import date
from modules.upload import Row


@pytest.mark.parametrize("scheme", ["FLS"])
@pytest.mark.parametrize("year", ["2019"])
class TestUpload:
    def test_create_candidate_data(
        self, year, scheme, test_upload_object, seed_data, test_session
    ):
        test_session.add_all(
            [
                Organisation(name="SIS"),
                Organisation(name="Foreign and Commonwealth Office"),
            ]
        )
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
        assert candidate.sexuality.value == "Bisexual"
        assert candidate.current_grade().value == "Grade 6 (or equivalent)"
        assert candidate.roles[0].date_started == date(2019, 1, 1)
        assert (
            candidate.most_recent_application().aspirational_grade.value
            == "SCS2 – Director"
        )

    @pytest.mark.parametrize(
        "csv_field, db_field, new_data",
        [
            ("Forename", "first_name", "[REDACTED - FIRST NAME]"),
            ("Surname_x", "last_name", "[REDACTED - LAST NAME]"),
        ],
    )
    def test_redact_replaces_personal_data_with_redacted(
        self,
        year,
        scheme,
        csv_field,
        db_field,
        new_data,
        test_upload_object,
        seed_data,
        test_session,
    ):
        test_session.add_all(
            [
                Organisation(name="SIS"),
                Organisation(name="Foreign and Commonwealth Office"),
            ]
        )
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
        self, year, scheme, test_session, test_upload_object, seed_data,
    ):
        existing_answers = [
            (Belief, "Agnostic"),
            (Sexuality, "Bisexual"),
            (Ethnicity, "White English/Welsh/Scottish/Northern Irish/British"),
            (Gender, "Male"),
        ]
        for answer in existing_answers:
            row_to_go = answer[0].query.filter_by(value=answer[1]).first()
            test_session.delete(row_to_go)
            # if these aren't taken out, there's a chance they'll be randomly chosen again
        test_session.add_all(
            [
                Organisation(name="SIS"),
                Organisation(name="Foreign and Commonwealth Office"),
            ]
        )
        u = test_upload_object(
            f"tests/data/{year}/test_csv.csv",
            f"tests/data/{year}/test_application_csv.csv",
            True,
            scheme,
        )
        u.complete_upload()
        candidate = Candidate.query.filter_by(email_address="PU007@gov.uk").first()
        assert candidate.sexuality.value != "Bisexual"
        assert candidate.belief.value != "Agnostic"
        assert (
            candidate.ethnicity.value
            != "White English/Welsh/Scottish/Northern Irish/British"
        )
        assert candidate.gender.value != "Male"
        assert candidate.main_job_type.value != "Don’t know"


class TestRow:
    def test_process_organisation_adds_alb_to_parent(self, blank_session):
        dept = "Foreign and Commonwealth Office"
        alb = "SIS"
        blank_session.add_all(
            [
                Organisation(id=1, name=alb, arms_length_body=True),
                Organisation(id=2, name=dept, department=True),
            ]
        )
        Row._process_organisation(dept, alb)
        assert (
            Organisation.query.filter_by(name=alb).first().parent_organisation_id == 2
        )

    def test_process_organisation_falls_back_to_dept_if_no_alb(self, blank_session):
        blank_session.add(Organisation(name="FCO"))
        org = Row._process_organisation("FCO", "Not Applicable")
        assert org.name == "FCO"
