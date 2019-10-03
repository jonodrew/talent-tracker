from app.models import *
from datetime import datetime, date
from typing import List
import pandas as pd
import random
import os


class Upload:
    def __init__(
        self,
        intake_filepath: str,
        programme: str,
        scheme_start_date: str,
        application_filepath: str,
    ):
        self.intake_filepath = os.path.abspath(intake_filepath)
        self.application_filepath = os.path.abspath(application_filepath)
        self.scheme: Scheme = Scheme.query.filter_by(name=programme).first()
        self.scheme_start_date = datetime.strptime(scheme_start_date, "%Y-%m-%d").date()
        self.intake_dataframe = pd.read_csv(self.intake_filepath)
        self.application_dataframe = pd.read_csv(self.application_filepath)
        self.joined_dataframe: pd.DataFrame = self.join_csvs()

    def complete_upload(self):
        for i in range(len(self.joined_dataframe.index)):
            row_series = self.joined_dataframe.iloc[i]
            row = Row(row_series, self.scheme_start_date, self.scheme)
            db.session.add(row.get_candidate())
        db.session.commit()

    def join_csvs(self):
        df = pd.merge(
            self.intake_dataframe,
            self.application_dataframe,
            left_on="Psych. Username",
            right_on="PerID",
            how="left",
            suffixes=("_intake", "_application"),
        )
        return df[df.Status == "Successful"]


class Row:
    def __init__(
        self, row: pd.Series, scheme_start_date: datetime.date, scheme: Scheme
    ):
        self.data = row
        self.candidate = self._create_candidate_data()
        self.scheme_start_date: date = scheme_start_date
        self.scheme = scheme

    def get_candidate(self):
        self._process_row()
        return self.candidate

    @staticmethod
    def _yes_is_true_no_is_false_translator(response: str) -> bool:
        return True if response == "Yes" else False

    @staticmethod
    def _empty_translator(cell: str) -> bool:
        return False if cell == "" else Row._yes_is_true_no_is_false_translator(cell)

    @staticmethod
    def _separate_email_addresses(cell_content: str) -> List[str]:
        for delim in ",;":
            cell_content = cell_content.replace(delim, " ")
        addresses = [address.strip() for address in cell_content.split()]
        return addresses

    def _process_row(self):
        self._add_application()
        self._add_most_recent_role()
        self._add_first_role()

    def _get_title_or_not_provided(self):
        title = self.data.get("Job Title")
        return "Not provided" if title == "" else title

    def _add_most_recent_role(self):
        self.candidate.roles.append(
            Role(
                role_name=self._get_title_or_not_provided(),
                organisation=Organisation.query.filter_by(
                    name=self.data.Department_intake
                ).first(),
                profession=Profession.query.filter_by(
                    value=self.data.Profession_intake
                ).first(),
                grade=Grade.query.filter_by(
                    value=self.data.get("Current Grade")[0:7]
                ).first(),
                location=Location.query.filter_by(
                    value=self.data.Location_intake
                ).first(),
                role_change=Promotion.query.filter_by(value="substantive").first(),
                date_started=date(self.scheme_start_date.year - 1, 1, 1),
            )
        )

    @staticmethod
    def _grade_processor(grade: str) -> Grade:
        if type(grade) is not str:
            return Grade.query.filter_by(value="Prefer not to say").first()
        else:
            return Grade.query.filter_by(value=grade).first()

    def _process_organisation(self, department_field, alb_field) -> Organisation:
        dept = self._get_org_or_create(department_field, dept=True)
        if alb_field == "Not Applicable":
            return dept
        else:
            alb = self._get_org_or_create(alb_field, alb=True)
            alb.parent_organisation_id = dept.id
            db.session.add(alb)
            return alb

    @staticmethod
    def _get_org_or_create(org_name: str, alb: bool = None, dept: bool = None):
        return Organisation.query.filter_by(name=org_name).first() or Organisation(
            name=org_name, arms_length_body=alb, department=dept
        )

    def _add_first_role(self):
        self.candidate.roles.append(
            Role(
                date_started=self.candidate.joining_date,
                role_name="Not given",
                grade=self.candidate.joining_grade,
                role_change=Promotion.query.filter_by(value="substantive").first(),
            )
        )

    def _create_candidate_data(self):
        c = Candidate(
            joining_date=date(self.data.get("CS Joining Year"), 1, 1),
            completed_fast_stream=self._yes_is_true_no_is_false_translator(
                self.data["Have you completed  Fast Stream?"]
            ),
            first_name=self.data.get("First Name"),
            last_name=self.data.get("Last Name_intake"),
            caring_responsibility=self._yes_is_true_no_is_false_translator(
                self.data.get("Caring Responsibility")
            ),
            long_term_health_condition=self._yes_is_true_no_is_false_translator(
                self.data.Disabled_intake
            ),
            age_range=AgeRange.query.filter_by(
                value=self.data.get("Age Group")
            ).first(),
            working_pattern=WorkingPattern.query.filter_by(
                value=self.data.get("Working Pattern")
            ).first(),
            belief=Belief.query.filter_by(
                value=self.data.get("Religion/Belief")
            ).first(),
            sexuality=Sexuality.query.filter_by(
                value=self.data.get("Sexual Orientation_application")
            ).first(),
            ethnicity=Ethnicity.query.filter_by(
                value=self.data.Ethnicity_application
            ).first(),
            main_job_type=MainJobType.query.filter_by(
                value=self.data.get(
                    "Describes the sort of work the main/ highest income earner in your household did in their main job?"
                )
            ).first(),
            gender=Gender.query.filter_by(value=self.data.Gender_intake).first(),
            joining_grade=Grade.query.filter_by(
                value=self.data.get("CS Joining Grade")
            ).first(),
        )
        addresses = self._separate_email_addresses(
            self.data.get("Email Address_application")
        )
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
                cohort=self.data.Cohort,
            )
        )


class RedactedRow(Row):
    def __init__(
        self, row: pd.Series, scheme_start_date: datetime.date, scheme: Scheme
    ):
        super().__init__(row, scheme_start_date, scheme)

    def _get_title_or_not_provided(self):
        return "[REDACTED-JOB TITLE]"

    def _create_candidate_data(self):
        c = Candidate(
            joining_date=date(self.data.get("CS Joining Year"), 1, 1),
            completed_fast_stream=self._yes_is_true_no_is_false_translator(
                self.data["Have you completed  Fast Stream?"]
            ),
            first_name="[REDACTED - FIRST NAME]",
            last_name="[REDACTED - LAST NAME]",
            caring_responsibility=self._yes_is_true_no_is_false_translator(
                self.data.get("Caring Responsibility")
            ),
            long_term_health_condition=random.randint(0, 1),
            age_range=AgeRange.query.filter_by(
                value=self.data.get("Age Group")
            ).first(),
            working_pattern=WorkingPattern.query.filter_by(
                value=self.data.get("Working Pattern")
            ).first(),
            belief=random.choice(Belief.query.all()),
            sexuality=random.choice(Sexuality.query.all()),
            ethnicity=random.choice(Ethnicity.query.all()),
            main_job_type=random.choice(MainJobType.query.all()),
            gender=random.choice(Gender.query.all()),
            joining_grade=Grade.query.filter_by(
                value=self.data.get("CS Joining Grade")
            ).first(),
        )
        addresses = self._separate_email_addresses(
            self.data.get("Email Address_application")
        )
        c.email_address = f"{self.data.PerID}@gov.uk"
        if len(addresses) > 1:
            c.secondary_email_address = "[REDACTED - EMAIL ADDRESS]"
        return c
