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
    return Candidate(
        email_address="staging.candidate@gov.uk",
        secondary_email_address="staging.secondary@gov.uk",
        joining_date=date(2015, 9, 1),
        first_name="Test",
        last_name="Candidate",
        completed_fast_stream=True,
        joining_grade=Grade.query.filter(Grade.value.like("%Faststream%")).first(),
        age_range_id=2,
        ethnicity_id=1,
        working_pattern_id=1,
        belief_id=1,
        gender_id=1,
        sexuality_id=1,
        roles=[
            Role(
                date_started=date(2015, 9, 2),
                profession_id=1,
                role_change_id=2,
                organisation_id=Organisation.query.filter(
                    Organisation.name == "Cabinet Office"
                )
                .first()
                .id,
                grade=Grade.query.filter(Grade.value.like("%Faststream%")).first(),
                location=Location.query.filter_by(value="London").first(),
            )
        ],
        applications=[Application(scheme_id=1, scheme_start_date=date(2018, 3, 1))],
    )


def generate_random_candidate():
    return Candidate(
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
        roles=[
            Role(
                date_started=date(2015, 9, 2),
                organisation_id=random.choice(Organisation.query.all()).id,
                grade=Grade.query.filter(Grade.value.like("%Faststream%")).first(),
                location=random.choice(Location.query.all()),
                role_change_id=2,
            )
        ],
        main_job_type=MainJobType.query.first(),
    )


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
    candidate.roles.extend(
        [
            Role(
                date_started=date(2018, 1, 1),
                role_change=Promotion.query.filter(
                    Promotion.value == "substantive"
                ).first(),
                organisation_id=14,
                location_id=2,
                role_name="First role",
                grade_id=5,
            ),
            Role(
                date_started=date(2019, 6, 1),
                role_change=Promotion.query.filter(
                    Promotion.value == f"{role_change_type}"
                ).first(),
                organisation_id=14,
                location_id=2,
                role_name="Second role",
                grade_id=4,
            ),
        ]
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
    db.session.add_all([Scheme(id=1, name="FLS"), Scheme(id=2, name="SLS")])
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
