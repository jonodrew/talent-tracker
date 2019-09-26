import random
from string import ascii_lowercase
from app.models import *
from datetime import date
import os


def random_string(length: int) -> str:
    return "".join([random.choice(ascii_lowercase) for i in range(length)])


def generate_random_fixed_data():

    organisation_names = [
        "Attorney General's Office",
        "The Charity Commission",
        "Competition Markets Authority",
        "Crown Prosecution Service",
        "Department for Business, Energy & Industrial Strategy",
        "Department for Digital, Culture, Media and Sport",
        "Department for Education",
        "Department for Environment Food and Rural Affairs (DEFRA)",
        "Department for Exiting the European Union",
        "Department for International Development",
        "Department for International Trade",
        "Department for Transport",
        "Department of Health and Social Care",
        "Food Standards Agency",
        "Foreign & Commonwealth Office",
        "Forestry Commission",
        "Government Actuary's Department",
        "Government Legal Department",
        "HM Land Registry",
        "HM Revenue & Customs",
        "HM Treasury",
        "Home Office",
        "Ministry of Defence",
        "Ministry of Housing, Communities and Local Govt",
        "Ministry of Justice",
        "The National Archives",
        "National Crime Agency",
        "Northern Ireland Office",
        "National Savings and Investments (NS&I)",
        "Office for Standards in Education (Ofsted)",
        "Office of Gas and Electricity Markets (Ofgem)",
        "Office of Qualifications and Examinations Regulation (Ofqual)",
        "Office of Rail and Road",
        "Other",
        "The Water Services Regulation Authority (Ofwat)",
        "Scottish Government",
        "Serious Fraud Office",
        "Supreme Court of the United Kingdom",
        "UK Export Finance",
        "UK Statistics Authority",
        "Welsh Government",
    ]

    organisations = [
        Organisation(id=i, name=value, department=True)
        for i, value in enumerate(organisation_names)
    ]
    professions = [
        "Communication",
        "Digital, data & technology",
        "Government Commercial Function",
        "Government Corporate Finance",
        "Government Economics Service",
        "Government Finance",
        "Government Legal Service",
        "Government Operational Research",
        "Government Property Profession",
        "Government Social Research",
        "Government Statistical Service",
        "Government Veterinary Profession",
        "Human Resources",
        "Intelligence Analysis",
        "Internal Audit",
        "Knowledge and Information Management",
        "Medical profession",
        "Operational delivery",
        "Other",
        "Planning professions",
        "Policy",
        "Prefer not to say",
        "Project delivery",
        "Psychology profession",
        "Science & engineering",
        "Security profession",
        "Tax",
    ]

    locations = [
        "East Midlands",
        "East of England",
        "London",
        "North East England",
        "North West England",
        "Northern Ireland",
        "Overseas",
        "Prefer not to say",
        "Scotland",
        "South East England",
        "South West England",
        "Wales",
        "West Midlands",
        "Yorkshire & the Humber",
    ]

    genders = [
        Gender(id=i, value=value)
        for i, value in enumerate(
            ["Male", "Female", "I identify in another way", "Prefer not to say"]
        )
    ]

    organisations.append(Organisation(id=len(organisations) + 1, name="Cabinet Office"))
    grades = [
        "Prefer not to say",
        "AA – Administrative Assistant",
        "AO – Administrative Officer",
        "EO – Executive Officer",
        "HEO – Higher Executive Officer",
        "HEO (D) – Faststream",
        "SEO – Senior Executive Officer",
        "Grade 7",
        "Grade 6",
        "SCS1 – Deputy Director",
        "SCS2 – Director",
        "SCS3 – Director General",
        "SCS 4 – Permanent Secretary",
    ]
    grades.reverse()

    bame_ethnic_groups = [
        "Any other Asian background",
        "Any other Black/African/Caribbean background",
        "Any other Ethnic background",
        "Any other mixed/multiple ethnic background",
        "Arab",
        "Asian or Asian British - Bangladeshi",
        "Asian or Asian British - Chinese",
        "Asian or Asian British - Indian",
        "Asian or Asian British - Pakistani",
        "Black or Black British African",
        "Black or Black British Caribbean",
        "Mixed - White and Asian",
        "Mixed - White and Black African",
        "Mixed - White and Black Caribbean",
        "White - Gypsy or Irish Traveller",
    ]
    non_bame_ethnic_groups = [
        "Any other white background",
        "Prefer not to say",
        "White - Irish",
        "White English/Welsh/Scottish/Northern Irish/British",
    ]
    sexual_orientation = [
        Sexuality(id=i, value=value)
        for i, value in enumerate(
            [
                "Bisexual",
                "Gay or lesbian",
                "I identify in another way",
                "Prefer not to say",
                "Straight/heterosexual",
            ]
        )
    ]
    ethnic_groups = [Ethnicity(value=item, bame=True) for item in bame_ethnic_groups]
    ethnic_groups.extend(
        [Ethnicity(value=item, bame=False) for item in non_bame_ethnic_groups]
    )
    for i, e in enumerate(ethnic_groups):
        e.id = i
    grades = [Grade(id=i, value=grade, rank=i) for i, grade in enumerate(grades)]
    professions = [
        Profession(id=i, value=string) for i, string in enumerate(professions)
    ]
    locations = [Location(id=i, value=string) for i, string in enumerate(locations)]
    beliefs = [
        Belief(id=i, value=string)
        for i, string in enumerate(
            [
                "Agnostic",
                "Buddhist",
                "Christian",
                "Hindu",
                "Jewish",
                "Muslim",
                "No Religion",
                "Other Religion",
                "Prefer Not To Say",
                "Sikh",
            ]
        )
    ]
    ages = [
        AgeRange(id=i, value=string)
        for i, string in enumerate(
            [
                "16-19",
                "20-24",
                "25-29",
                "30-34",
                "35-39",
                "40-44",
                "45-49",
                "50-54",
                "55-59",
                "60-64",
            ]
        )
    ]
    working_patterns = [
        WorkingPattern(id=i, value=string)
        for i, string in enumerate(
            [
                "Full time",
                "Job share",
                "Part time",
                "Prefer not to say",
                "Flexible working",
                "Term time",
            ]
        )
    ]

    promotions = [
        Promotion(id=1, value="temporary"),
        Promotion(id=2, value="substantive"),
        Promotion(id=3, value="level transfer"),
        Promotion(id=4, value="demotion"),
    ]

    return {
        "organisations": organisations,
        "grades": grades,
        "professions": professions,
        "locations": locations,
        "ethnicities": ethnic_groups,
        "schemes": [Scheme(id=1, name="FLS"), Scheme(id=2, name="SLS")],
        "ages": ages,
        "genders": genders,
        "sexuality": sexual_orientation,
        "beliefs": beliefs,
        "working_patterns": working_patterns,
        "promotions": promotions,
        "job_types": [
            MainJobType(
                id=1, value="Civil Servant", lower_socio_economic_background=True
            )
        ],
    }


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


def commit_data():
    for key, value in generate_random_fixed_data().items():
        db.session.add_all(value)
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
