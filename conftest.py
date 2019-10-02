import pytest
from datetime import date
from app import create_app
from app.models import db as _db
from config import TestConfig
from app.models import *
from modules.seed import clear_old_data, commit_data


@pytest.fixture(scope="session", autouse=True)
def test_client():
    flask_app = create_app(TestConfig)

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.test_request_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()


@pytest.fixture(scope="session")
def db(test_client):
    _db.app = test_client
    _db.create_all()

    yield _db

    _db.drop_all()


@pytest.fixture(scope="function", autouse=True)
def test_session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session_ = db.create_scoped_session(options=options)

    db.session = session_

    test_user = User(email="Test User")
    test_user.set_password("Password")
    db.session.add(test_user)

    db.session.add_all([Scheme(id=1, name="FLS"), Scheme(id=2, name="SLS")])
    db.session.add_all(
        [
            Promotion(id=1, value="substantive promotion"),
            Promotion(id=2, value="temporary promotion"),
            Promotion(id=3, value="level transfer"),
            Promotion(id=4, value="demotion"),
        ]
    )
    db.session.add_all(
        [
            Grade(id=2, value="Grade 7", rank=6),
            Grade(id=3, value="Grade 6", rank=5),
            Grade(id=4, value="Deputy Director (SCS1)", rank=4),
            Grade(id=1, value="Admin Assistant (AA)", rank=7),
        ]
    )
    db.session.add(Candidate(id=1))
    db.session.commit()

    yield session_

    transaction.rollback()
    connection.close()
    session_.remove()


@pytest.fixture
def test_candidate(test_session):
    candidate = Candidate.query.get(1)
    candidate.email_address = "test.candidate@numberten.gov.uk"
    candidate.secondary_email_address = "test.secondary@gov.uk"
    candidate.first_name = "Testy"
    candidate.last_name = "Candidate"
    candidate.completed_fast_stream = True
    candidate.joining_date = date(2010, 5, 1)
    candidate.joining_grade_id = 1
    candidate.gender_id = 1
    candidate.ethnicity_id = 1
    candidate.working_pattern_id = 1
    candidate.belief_id = 1
    candidate.sexuality_id = 1

    candidate.roles.append(
        Role(date_started=date(2010, 5, 1), grade_id=2, location_id=1, role_change_id=2)
    )
    test_data = {
        "grades": [
            Grade(id=10, value="Band A", rank=2),
            Grade(id=11, value="SCS3", rank=1),
        ],
        "test_candidates": [candidate],
        "locations": [Location(id=1, value="Test")],
    }
    for key in test_data.keys():
        test_session.add_all(test_data.get(key))
        test_session.commit()
    yield Candidate.query.first()


@pytest.fixture
def test_candidate_applied_to_fls(test_candidate, test_session):
    test_candidate.applications.append(
        Application(
            application_date=date(2019, 6, 1),
            scheme_id=1,
            scheme_start_date=date(2020, 3, 1),
        )
    )
    test_session.add(test_candidate)
    test_session.commit()
    yield Candidate.query.first()


@pytest.fixture
def test_candidate_applied_and_promoted(test_candidate_applied_to_fls, test_session):
    test_candidate_applied_to_fls.roles.append(
        Role(date_started=date(2020, 1, 1), role_change_id=2)
    )
    test_session.add(test_candidate_applied_to_fls)
    test_session.commit()
    yield


@pytest.fixture
def test_roles(test_session, test_candidate):
    roles = [
        Role(
            date_started=date(2019, 1, 1),
            candidate_id=test_candidate.id,
            grade_id=Grade.query.filter(Grade.value == "Band A").first().id,
        )
    ]
    test_session.add_all(roles)
    test_session.commit()
    yield


@pytest.fixture
def test_locations(test_session):
    locations = [Location(value="The North"), Location(value="The South")]
    test_session.add_all(locations)
    test_session.commit()
    yield


@pytest.fixture
def test_orgs(test_session):
    test_session.add_all(
        [Organisation(name="Organisation 1"), Organisation(name="Organisation 2")]
    )
    test_session.commit()
    yield


@pytest.fixture
def test_professions(test_session):
    test_session.add_all(
        [Profession(value="Profession 1"), Profession(value="Profession 2")]
    )
    test_session.commit()
    yield


@pytest.fixture
def test_ethnicities(test_session):
    test_session.add_all(
        [
            Ethnicity(id=2, value="White British"),
            Ethnicity(id=3, value="Black British", bame=True),
        ]
    )
    test_session.commit()
    yield


@pytest.fixture
def test_multiple_candidates_multiple_ethnicities(test_session, test_ethnicities):
    test_session.add_all(
        [Candidate(ethnicity=Ethnicity.query.get(3)) for i in range(10)]
    )
    test_session.add_all(
        [Candidate(ethnicity=Ethnicity.query.get(2)) for i in range(10)]
    )
    test_session.commit()
    yield


@pytest.fixture
def gender_ten_of_each(test_session):
    candidates = []
    for gender in Gender.query.all():
        for i in range(10):
            candidates.append(Candidate(gender=gender))
    test_session.add_all(candidates)
    test_session.commit()
    yield


@pytest.fixture
def disability_with_without_no_answer(test_session):
    output = []
    for i in range(29):
        if i % 3 == 0:
            output.append(Candidate(long_term_health_condition=True))
        elif i % 3 == 1:
            output.append(Candidate(long_term_health_condition=False))
        else:
            output.append(Candidate(long_term_health_condition=None))
    test_session.add_all(output)
    test_session.commit()
    yield


@pytest.fixture
def candidates_promoter():
    def _promoter(candidates_to_promote, decimal_ratio, temporary=False):
        if temporary:
            change_type = Promotion.query.filter(
                Promotion.value == "temporary promotion"
            ).first()
        else:
            change_type = Promotion.query.filter(
                Promotion.value == "substantive promotion"
            ).first()
        for candidate in candidates_to_promote[
            0 : int(len(candidates_to_promote) * decimal_ratio)
        ]:
            candidate.roles.extend(
                [
                    Role(date_started=date(2018, 1, 1)),
                    Role(date_started=date(2019, 3, 1), role_change=change_type),
                ]
            )
        return candidates_to_promote

    return _promoter


@pytest.fixture
def scheme_appender(test_session):
    def _add_scheme(candidates_to_add, scheme_id_to_add=1, meta=False, delta=False):
        for candidate in candidates_to_add:
            candidate.applications.append(
                Application(
                    application_date=date(2018, 8, 1),
                    scheme_id=scheme_id_to_add,
                    scheme_start_date=date(2019, 3, 1),
                    meta=meta,
                    delta=delta,
                )
            )

    return _add_scheme


@pytest.fixture
def detailed_candidate(test_candidate, test_session):
    test_candidate: Candidate
    test_session.add(Organisation(id=1, name="Department of Fun"))
    test_session.add(Location(id=2, value="Stargate-1"))
    test_session.add(WorkingPattern(id=1, value="24/7"))
    test_session.add(Belief(id=1, value="Don't forget to be awesome"))
    test_session.add(Sexuality(id=1, value="Pan"))
    test_session.add(Ethnicity(id=1, value="Terran", bame=True))
    test_session.add_all(
        [
            Gender(id=1, value="Fork"),
            Gender(id=2, value="Knife"),
            Gender(id=3, value="Chopsticks"),
        ]
    )
    test_session.add(Grade(id=5, value="Director (SCS2)", rank=3))
    test_session.add(
        MainJobType(id=1, value="Roboticist", lower_socio_economic_background=True)
    )
    test_session.add(AgeRange(id=1, value="Immortal"))

    test_candidate.joining_date = date(2018, 9, 1)
    test_candidate.joining_grade_id = 1
    test_candidate.main_job_type_id = 1
    test_candidate.working_pattern_id = 1
    test_candidate.belief_id = 1
    test_candidate.age_range_id = 1
    test_candidate.caring_responsibility = True
    test_candidate.long_term_health_condition = True

    test_candidate.applications.append(
        Application(
            application_date=date(2018, 6, 1),
            scheme_start_date=date(2019, 3, 1),
            meta=True,
            delta=False,
            cohort=1,
            scheme_id=1,
        )
    )
    test_candidate.roles.extend(
        [
            Role(date_started=date(2018, 6, 1)),
            Role(
                date_started=date(2019, 1, 1),
                role_change_id=1,
                role_name="Director of Happiness",
                grade_id=5,
                location_id=2,
                organisation_id=1,
            ),
        ]
    )


@pytest.fixture
def logged_in_user(test_client):
    with test_client:
        test_client.post(
            "/auth/login", data={"email-address": "Test User", "password": "Password"}
        )
        yield
        test_client.get("/auth/logout")


@pytest.fixture
def seed_data(test_client):
    with test_client:
        clear_old_data()
        commit_data()
        yield
        clear_old_data()
