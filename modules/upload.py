import csv
from app.models import Candidate, Role, Scheme, Grade, Gender, Ethnicity, Sexuality, Organisation, Profession, db, \
    Location, Promotion, Application
import datetime


class Upload:
    def __init__(self, filepath: str, programme: str, scheme_start_date: str):
        with open(filepath, 'r') as f:
            self.file_content = list(csv.DictReader(f))
        self.scheme: Scheme = Scheme.query.filter_by(name=programme).first()
        self.scheme_start_date = scheme_start_date

    def long_term_health_condition_translation(self, response: str):
        return True if response == 'Yes' else False

    def create_candidate_data_row(self, row: dict):
        c = Candidate(
            first_name=row.get('First Name'), last_name=row.get('Last Name'), email_address=row.get('Email Address'),
            sexuality=Sexuality.query.filter_by(value=row.get('Sexual Orientation')).first(),
            long_term_health_condition=self.long_term_health_condition_translation(row.get('Disability')),
            gender=Gender.query.filter_by(value=row.get('Gender')).first(),
            joining_grade=Grade.query.filter_by(value=row.get('Original Grade')).first(),
            ethnicity=Ethnicity.query.filter_by(value=row.get('Ethnicity')).first(),
            roles=[
                Role(
                    date_started=datetime.date(2019, 1, 1), role_name=row.get('Job Title'),
                    organisation=Organisation.query.filter_by(name=row.get('Department')).first(),
                    profession=Profession.query.filter_by(value=row.get('Profession')),
                    location=Location.query.filter_by(value=row.get('Location')),
                    grade=Grade.query.filter_by(value=row.get('Current Grade')).first(),
                    role_change=Promotion.query.filter_by(value='substantive')
                )
            ],
            applications=[
                Application(
                    scheme_id=self.scheme.id, scheme_start_date=self.scheme_start_date, successful=True,
                    meta=row.get('META'), delta=row.get('DELTA'), cohort=row.get('Cohort')
                )
            ]
        )
        return c

    def complete_upload(self):
        for row in self.file_content:
            db.session.add(self.create_candidate_data_row(row))
        db.session.commit()