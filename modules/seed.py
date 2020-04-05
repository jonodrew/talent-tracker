import random
from string import ascii_lowercase
from typing import Dict, Tuple
from app.models import *
from datetime import date
import os
import pandas as pd


def random_string(length: int) -> str:
    return "".join([random.choice(ascii_lowercase) for i in range(length)])


def generate_known_candidate():
    c = Candidate(
        email_address="staging.candidate@gov.uk",
        secondary_email_address="staging.secondary@gov.uk",
        joining_date=date(2015, 9, 1),
        first_name="Test",
        last_name="Candidate",
        completed_fast_stream=True,
        joining_grade=Grade.query.filter(Grade.value.like("%Faststream%")).first(),
        age_range=AgeRange.query.filter_by(value="25-29").first(),
        ethnicity=Ethnicity.query.filter_by(value="Arab").first(),
        working_pattern=WorkingPattern.query.filter_by(value="Full time").first(),
        belief=Belief.query.filter_by(value="No Religion").first(),
        gender=Gender.query.filter_by(value="Prefer not to say").first(),
        sexuality=Sexuality.query.filter_by(value="Bisexual").first(),
        applications=[
            Application(
                scheme_id=Scheme.query.filter_by(name="FLS").first().id,
                scheme_start_date=date(2018, 3, 1),
            )
        ],
    )
    c.new_role(
        start_date=date(2015, 9, 2),
        new_org_id=Organisation.query.filter(Organisation.name == "Cabinet Office")
        .first()
        .id,
        new_profession_id=Profession.query.filter_by(value="Digital, data & technology")
        .first()
        .id,
        new_location_id=Location.query.filter_by(value="London").first().id,
        new_grade_id=Grade.query.filter(Grade.value.like("%Faststream%")).first().id,
        new_title="Known role",
        role_change_id=2,
    )
    return c


def generate_random_candidate():
    c = Candidate(
        email_address=f"{random_string(16)}@gov.uk",
        first_name=f"{random_string(8)}",
        last_name=f"{random_string(12)}",
        joining_date=date(
            random.randrange(1960, 2018),
            random.randrange(1, 12),
            random.randrange(1, 28),
        ),
        completed_fast_stream=random.choice([True, False]),
        joining_grade=(Grade.query.filter_by(rank=6).first()),
        ethnicity=random.choice(Ethnicity.query.all()),
        age_range=random.choice(AgeRange.query.all()),
        gender_id=random.choice(Gender.query.all()).id,
        long_term_health_condition=random.choice([True, False, False]),
        caring_responsibility=random.choice([True, False, False]),
        belief=random.choice(Belief.query.all()),
        sexuality=random.choice(Sexuality.query.all()),
        working_pattern=random.choice(WorkingPattern.query.all()),
        main_job_type=MainJobType.query.first(),
    )
    c.new_role(
        start_date=date(2015, 9, 2),
        new_org_id=random.choice(Organisation.query.all()).id,
        new_profession_id=random.choice(Profession.query.all()).id,
        new_location_id=random.choice(Location.query.all()).id,
        new_grade_id=Grade.query.filter(Grade.value.like("%Faststream%")).first().id,
        new_title=f"Random role {random_string(10)}",
        role_change_id=2,
    )
    return c


def apply_candidate_to_scheme(
    scheme_name: str,
    candidate: Candidate,
    meta=False,
    delta=False,
    scheme_start_date=date(2018, 3, 1),
):
    candidate.applications.append(
        Application(
            scheme_id=Scheme.query.filter_by(name=scheme_name).first().id,
            successful=True,
            meta=meta,
            delta=delta,
            scheme_start_date=scheme_start_date,
        )
    )
    return candidate


def promote_candidate(candidate: Candidate, role_change_type=None):
    if role_change_type is None:
        role_change_type = random.choice(["substantive", "temporary", "level transfer"])
    candidate.new_role(
        start_date=date(2018, 1, 1),
        new_org_id=Organisation.query.filter_by(name="Cabinet Office").first().id,
        new_profession_id=1,
        new_location_id=Location.query.filter_by(value="London").first().id,
        new_grade_id=Grade.query.filter_by(rank=5).first().id,
        new_title="First role",
        role_change_id=Promotion.query.filter(Promotion.value == "substantive")
        .first()
        .id,
    )
    candidate.new_role(
        start_date=date(2019, 6, 1),
        new_org_id=Organisation.query.filter_by(name="Cabinet Office").first().id,
        new_profession_id=1,
        new_location_id=Location.query.filter_by(value="London").first().id,
        new_grade_id=Grade.query.filter_by(rank=4).first().id,
        new_title="Second role",
        role_change_id=Promotion.query.filter(Promotion.value == f"{role_change_type}")
        .first()
        .id,
    )
    return candidate


def random_candidates(scheme: str, number: int):
    return [
        apply_candidate_to_scheme(scheme, generate_random_candidate())
        for i in range(number)
    ]


class SeedData:
    def __init__(self, path_to_spreadsheet: str):
        self.dict_of_dataframes: Dict[str, pd.DataFrame] = pd.read_excel(
            path_to_spreadsheet, sheet_name=None
        )
        self.sheets_to_upload = [
            ("Department", Organisation),
            ("ALB", Organisation),
            ("Gender", Gender),
            ("Sexual Orientation", Sexuality),
            ("Ethnicity", Ethnicity),
            ("Grade", Grade),
            ("Profession", Profession),
            ("Location", Location),
            ("Age", AgeRange),
            ("ReligionBelief", Belief),
            ("Work Pattern", WorkingPattern),
            ("main job type", MainJobType),
        ]

    def seed_data(self):
        for sheet in self.sheets_to_upload:
            db.session.add_all(self._process_from_spreadsheet(sheet))
        db.session.add_all([Scheme(id=3, name="FLS"), Scheme(id=4, name="SLS")])
        db.session.add_all(
            [
                Promotion(id=1, value="temporary"),
                Promotion(id=2, value="substantive"),
                Promotion(id=3, value="level transfer"),
                Promotion(id=4, value="demotion"),
            ]
        )
        db.session.commit()

    def _process_from_spreadsheet(self, sheet_data_tuple: Tuple[str, db.Model]):
        sheet_as_df = self.dict_of_dataframes.get(sheet_data_tuple[0])
        output = sheet_as_df.apply(
            self._process_row, args=(sheet_data_tuple[1],), axis=1
        )
        return list(output)

    def _process_row(self, row_as_series: pd.Series, model: db.Model):
        value_or_name = row_as_series.keys()[0]
        r = model()
        setattr(r, value_or_name, row_as_series[0])
        if len(row_as_series.keys()) > 1:
            secondary_attribute = row_as_series.keys()[1]
            setattr(r, secondary_attribute, row_as_series[secondary_attribute])
        return r


def commit_data(seed_data_filepath: str):
    SeedData(seed_data_filepath).seed_data()
    known_candidate = generate_known_candidate()
    db.session.add(known_candidate)

    random_promoted_fls_candidates = [
        promote_candidate(candidate) if i % 2 == 0 else candidate
        for i, candidate in enumerate(random_candidates("FLS", 100))
    ]
    random_promoted_sls_candidates = [
        promote_candidate(candidate) if i % 2 == 0 else candidate
        for i, candidate in enumerate(random_candidates("SLS", 100))
    ]
    candidates = random_promoted_sls_candidates + random_promoted_fls_candidates
    ethnic_minority_background = Ethnicity.query.filter(Ethnicity.bame.is_(True)).all()

    for candidate in candidates:
        coin_flip = random.choice([True, False])
        if candidate.ethnicity in ethnic_minority_background:
            candidate.applications[0].meta = coin_flip
        if candidate.long_term_health_condition:
            candidate.applications[0].delta = coin_flip
    if os.environ.get("ENV") == "dev":
        u = User(email="developer@talent-tracker.gov.uk")
        u.set_password("talent-tracker")
        db.session.add(u)

    db.session.add_all(candidates)
    db.session.commit()


def clear_old_data():
    tables = [
        Application,
        Role,
        Candidate,
        Organisation,
        Profession,
        Grade,
        Location,
        Ethnicity,
        Scheme,
        AgeRange,
        Gender,
        Sexuality,
        AgeRange,
        Belief,
        WorkingPattern,
        Promotion,
        AuditEvent,
        MainJobType,
    ]
    for table in tables:
        table.query.delete()
        db.session.commit()
    if os.environ.get("ENV") == "dev":
        User.query.delete()
        db.session.commit()
