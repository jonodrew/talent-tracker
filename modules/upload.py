from app.models import *
from datetime import datetime, date
from typing import List
import pandas as pd


class Upload:
    def __init__(
        self,
        intake_filepath: str,
        programme: str,
        scheme_start_date: str,
        application_filepath: str,
    ):
        self.intake_filepath = intake_filepath
        self.application_filepath = application_filepath
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
        return pd.merge(
            self.intake_dataframe,
            self.application_dataframe,
            left_on="Psych. Username",
            right_on="PerID",
            how="left",
        )


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
        self._add_first_role()

    def _get_title_or_not_provided(self):
        title = self.data.get("Job Title")
        return "Not provided" if title == "" else title

    def _add_most_recent_role(self):
        self.candidate.roles.append(
            Role(
                role_name=self._get_title_or_not_provided(),
                organisation_id=Organisation.query.filter_by(
                    name=self.data.Department_x
                )
                .first()
                .id,
                profession=Profession.query.filter_by(
                    value=self.data.Profession_x
                ).first(),
                grade=Grade.query.filter_by(
                    value=self.data.get("Current Grade")[0:7]
                ).first(),
                location=Location.query.filter_by(value=self.data.Location_x).first(),
                role_change=Promotion.query.filter_by(value="substantive").first(),
                date_started=date(self.scheme_start_date.year - 1, 1, 1),
            )
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
            last_name=self.data.get("Last Name_x"),
            caring_responsibility=self._yes_is_true_no_is_false_translator(
                self.data.get("Caring Responsibility")
            ),
            long_term_health_condition=self._yes_is_true_no_is_false_translator(
                self.data.Disabled_x
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
                value=self.data.get("Sexual Orientation_y")
            ).first(),
            ethnicity=Ethnicity.query.filter_by(value=self.data.Ethnicity_y).first(),
            main_job_type=MainJobType.query.filter_by(
                value=self.data.get(
                    "Describes the sort of work the main/ highest income earner in your household did in their main job?"
                )
            ).first(),
            gender=Gender.query.filter_by(value=self.data.Gender_x).first(),
            joining_grade=Grade.query.filter_by(
                value=self.data.get("CS Joining Grade")
            ).first(),
        )
        addresses = self._separate_email_addresses(self.data.get("Email Address_y"))
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
