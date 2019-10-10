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
        redact_personal_data=True,
    ):
        self.intake_filepath = os.path.abspath(intake_filepath)
        self.application_filepath = os.path.abspath(application_filepath)
        self.scheme: Scheme = Scheme.query.filter_by(name=programme).first()
        self.scheme_start_date = datetime.strptime(scheme_start_date, "%Y-%m-%d").date()
        self.intake_dataframe = pd.read_csv(self.intake_filepath)
        self.application_dataframe = pd.read_csv(self.application_filepath)
        self.joined_dataframe: pd.DataFrame = self.join_csvs()
        self.row_reader = RedactedRow if redact_personal_data else Row

    def complete_upload(self):
        for i in range(len(self.joined_dataframe.index)):
            row_series = self.joined_dataframe.iloc[i]
            row = self.row_reader(row_series, self.scheme_start_date, self.scheme)
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
        self._add_email_address()
        self._collect_personal_data()
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
                organisation=self._process_organisation(
                    self.data.Department_intake, self.data.ALB
                ),
                profession=Profession.query.filter_by(
                    value=self.data.Profession_intake
                ).first(),
                grade=self._grade_processor(self.data.get("Current Grade")),
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

    @staticmethod
    def _process_organisation(department_field, alb_field) -> Organisation:
        dept = Row._get_org_or_create(department_field, dept=True)
        if alb_field == "Not Applicable":
            return dept
        else:
            alb = Row._get_org_or_create(alb_field, alb=True)
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

    @staticmethod
    def time_parser(datetime_string: str):
        if type(datetime_string) is float:
            return None
        if len(datetime_string) > 4:
            return datetime.strptime(datetime_string[0:10], "%Y-%m-%d")
        else:
            return date(int(datetime_string), 1, 1)

    def _create_candidate_data(self):
        print("Processing successful candidate")
        print(f"Creating candidate PerID {self.data.get('Psych. Username')}")
        c = Candidate(
            joining_date=self.time_parser(self.data.get("CS Joining Year")),
            completed_fast_stream=self._yes_is_true_no_is_false_translator(
                self.data["Have you completed  Fast Stream?"]
            ),
            caring_responsibility=self._yes_is_true_no_is_false_translator(
                self.data.get("Caring Responsibility")
            ),
            working_pattern=WorkingPattern.query.filter_by(
                value=self.data.get("Working Pattern")
            ).first(),
            joining_grade=Grade.query.filter_by(
                value=self.data.get("CS Joining Grade")
            ).first(),
        )
        return c

    def _aspiration_processor(self):
        if self.data.get("Aspiration") == "Remain at Grade":
            return Grade.query.filter_by(value=self.data.get("Current Grade")).first()
        else:
            return Row._grade_processor(self.data.get("Aspiration"))

    def _add_application(self):
        self.candidate.applications.append(
            Application(
                scheme_id=self.scheme.id,
                scheme_start_date=self.scheme_start_date,
                successful=True,
                meta=self._empty_translator(self.data.get("META", False)),
                delta=self._empty_translator(self.data.get("DELTA", False)),
                cohort=self.data.Cohort,
                aspirational_grade=self._grade_processor(self.data.Aspiration),
            )
        )

    def _collect_personal_data(self):
        self.candidate.first_name = self.data.get("First Name")
        self.candidate.last_name = self.data.get("Last Name_intake")
        self.candidate.belief = Belief.query.filter_by(
            value=self.data.get("Religion/Belief")
        ).first()
        self.candidate.sexuality = Sexuality.query.filter_by(
            value=self.data.get("Sexual Orientation_application")
        ).first()
        self.candidate.ethnicity = Ethnicity.query.filter_by(
            value=self.data.Ethnicity_application
        ).first()
        self.candidate.main_job_type = MainJobType.query.filter_by(
            value=self.data.get(
                "Describes the sort of work the main/ highest income earner in your household did in their main job?"
            )
        ).first()
        self.candidate.gender = Gender.query.filter_by(
            value=self.data.Gender_intake
        ).first()
        self.long_term_health_condition = self._yes_is_true_no_is_false_translator(
            self.data.Disabled_intake
        )
        self.candidate.age_range = AgeRange.query.filter_by(
            value=self.data.get("Age Group")
        ).first()

    def _add_email_address(self):
        addresses = self._separate_email_addresses(
            self.data.get("Email Address_application")
        )
        self.candidate.email_address = addresses[0]
        if len(addresses) > 1:
            self.candidate.secondary_email_address = addresses[1]


class RedactedRow(Row):
    def __init__(
        self, row: pd.Series, scheme_start_date: datetime.date, scheme: Scheme
    ):
        super().__init__(row, scheme_start_date, scheme)

    def _get_title_or_not_provided(self):
        return "[REDACTED-JOB TITLE]"

    def _collect_personal_data(self):
        self.candidate.first_name = "[REDACTED - FIRST NAME]"
        self.candidate.last_name = "[REDACTED - LAST NAME]"
        self.candidate.belief = random.choice(Belief.query.all())
        self.candidate.sexuality = random.choice(Sexuality.query.all())
        self.candidate.ethnicity = random.choice(Ethnicity.query.all())
        self.candidate.main_job_type = random.choice(MainJobType.query.all())
        self.candidate.gender = random.choice(Gender.query.all())
        self.candidate.long_term_health_condition = random.randint(0, 1)
        self.candidate.age_range = random.choice(AgeRange.query.all())

    def _add_email_address(self):
        self.candidate.email_address = f"{self.data.PerID}@gov.uk"
