from reporting.base_report import Report
from typing import List
from app.models import Candidate, Application, Promotion, Role
from sqlalchemy import and_, extract
from datetime import datetime, date


class DetailedReport(Report):
    """
    The initial version of the detailed report will take one input year, one scheme, and one role_change_type
    """

    def __init__(self, intake_year: str, scheme: str, role_change_type: int):
        super().__init__(scheme)
        self.intake = int(intake_year)
        self.role_change_type: Promotion = Promotion.query.get(role_change_type)
        self.filename = (
            f"detailed-report-{self.intake}-{self.role_change_type.value}-{scheme}"
        )
        self.promoted_before_date = datetime.today()
        self.headers = [
            "candidate name",
            "candidate email",
            "candidate secondary email",
            "cohort",
            "offer",
            "current role title",
            "current grade",
            "current location",
            "current department",
            "joining date",
            "joining grade",
            "completed Fast Stream",
            "ethnic background",
            "from a minority ethnic background",
            "has a disability",
            "from a lower socio-economic background",
            "gender",
            "sexuality",
            "has caring responsibilities",
            "age range",
            "belief",
            "working pattern",
            "profile",
        ]

    def write_row(self, row_data, data_object, csv_writer):
        print(row_data)
        csv_writer.writerow(row_data)
        return data_object.getvalue()

    def row_writer(self, candidate: Candidate) -> List:
        application = candidate.most_recent_application()
        current_role: Role = candidate.current_role()
        return [
            f"{candidate.first_name} {candidate.last_name}",
            candidate.email_address,
            candidate.secondary_email_address,
            application.cohort,
            application.offer_status(),
            current_role.role_name,
            current_role.grade.value,
            current_role.location.value,
            current_role.organisation.name,
            candidate.joining_date,
            candidate.joining_grade.value,
            candidate.completed_fast_stream,
            candidate.ethnicity.value,
            candidate.ethnicity.bame,
            candidate.long_term_health_condition,
            candidate.main_job_type.lower_socio_economic_background,
            candidate.gender.value,
            candidate.sexuality.value,
            candidate.caring_responsibility,
            candidate.age_range.value,
            candidate.belief.value,
            candidate.working_pattern.value,
            f"localhost:5000/candidates/candidate/{candidate.id}",
        ]

    def get_data(self):
        output = []
        for candidate in self.candidates():
            output.append(self.row_writer(candidate))
        return output

    def candidates(self):
        """
        Iterate through the roles each candidate has held since beginning the programme and identifies if any of them
        have been 'role_change_type'. If they have, return that candidate
        :return:
        :rtype:
        """
        return [
            candidate
            for candidate in self.eligible_candidates()
            if self.role_change_type.id
            in {
                rce.role_change_id
                for rce in candidate.role_change_events_since_date(
                    date(self.intake, 1, 1)
                )
            }
        ]

    def eligible_candidates(self) -> List[Candidate]:
        """
        Eligible candidates are those in `intake` and on `scheme`. The year in the application start date is used as
        shorthand for the intake year
        :return: List[Candidate]
        """
        return [
            application.candidate
            for application in Application.query.filter(
                and_(
                    extract("year", Application.scheme_start_date) == self.intake,
                    Application.scheme_id == self.scheme.id,
                )
            ).all()
        ]
