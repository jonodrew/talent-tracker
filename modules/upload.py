import csv
from app.models import (
    Candidate,
    Role,
    Scheme,
    Grade,
    Gender,
    Ethnicity,
    Sexuality,
    Organisation,
    Profession,
    db,
    Location,
    Promotion,
    Application,
)
from datetime import datetime
from typing import List


class Upload:
    def __init__(self, intake_filepath: str, programme: str, scheme_start_date: str):
        with open(intake_filepath, "r") as f:
            self.intake_file_content = list(csv.DictReader(f))
        self.scheme: Scheme = Scheme.query.filter_by(name=programme).first()
        self.scheme_start_date = datetime.strptime(scheme_start_date, "%Y-%m-%d").date()

    def complete_upload(self):
        for row in self.intake_file_content:
            row = IntakeRow(row, self.scheme_start_date, self.scheme)
            db.session.add(row.get_candidate())
        db.session.commit()


class IntakeRow:
    def __init__(self, row: dict, scheme_start_date: datetime.date, scheme: Scheme):
        self.data = row
        self.candidate = self._create_candidate_data()
        self.scheme_start_date = scheme_start_date
        self.scheme = scheme

    def get_candidate(self):
        self._process_row()
        return self.candidate

    @staticmethod
    def _long_term_health_condition_translation(response: str) -> bool:
        return True if response == "Yes" else False

    @staticmethod
    def _empty_translator(cell: str) -> bool:
        return False if cell == "" else True

    @staticmethod
    def _separate_email_addresses(cell_content: str) -> List[str]:
        for delim in ",;":
            cell_content = cell_content.replace(delim, " ")
        addresses = [address.strip() for address in cell_content.split()]
        return addresses

    def _process_row(self):
        self._add_application()
        self._add_most_recent_role()

    def _get_title_or_not_provided(self):
        title = self.data.get("Job Title")
        return "Not provided" if title == "" else title

    def _add_most_recent_role(self):
        self.candidate.roles.append(
            Role(
                role_name=self._get_title_or_not_provided(),
                organisation_id=Organisation.query.filter_by(
                    name=self.data.get("Department")
                )
                .first()
                .id,
                profession=Profession.query.filter_by(
                    value=self.data.get("Profession")
                ).first(),
                grade=Grade.query.filter_by(
                    value=self.data.get("Current Grade")
                ).first(),
                location=Location.query.filter_by(
                    value=self.data.get("Location")
                ).first(),
                role_change=Promotion.query.filter_by(value="substantive").first(),
            )
        )

    def _create_candidate_data(self):
        c = Candidate(
            first_name=self.data.get("First Name"),
            last_name=self.data.get("Last Name"),
            sexuality=Sexuality.query.filter_by(
                value=self.data.get("Sexual Orientation")
            ).first(),
            long_term_health_condition=self._long_term_health_condition_translation(
                self.data.get("Disability")
            ),
            gender=Gender.query.filter_by(value=self.data.get("Gender")).first(),
            joining_grade=Grade.query.filter_by(
                value=self.data.get("Original Grade")
            ).first(),
            ethnicity=Ethnicity.query.filter_by(
                value=self.data.get("Ethnicity")
            ).first(),
        )
        addresses = self._separate_email_addresses(self.data.get("Email Address"))
        c.email_address = addresses[0]
        if len(addresses) > 1:
            c.secondary_email_address = addresses[1]
        return c

    def _add_application(self):
        self.candidate.applications.append(
            Application(
                scheme_id=self.scheme.id,
                scheme_start_date=self.scheme_start_date,
                successful=True,
                meta=self._empty_translator(self.data.get("META", False)),
                delta=self._empty_translator(self.data.get("DELTA", False)),
                cohort=self.data.get("Cohort"),
            )
        )
