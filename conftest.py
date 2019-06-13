import pytest
from datetime import date
from app import create_app
from app.models import db as _db
from config import TestConfig
from app.models import *
from modules.seed import clear_old_data, commit_data


@pytest.fixture(scope='session', autouse=True)
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


@pytest.fixture(scope='session')
def db(test_client):
    _db.app = test_client
    _db.create_all()

    yield _db

    _db.drop_all()


@pytest.fixture(scope='function', autouse=True)
def test_session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session_ = db.create_scoped_session(options=options)

    db.session = session_

    test_user = User(email='Test User')
    test_user.set_password("Password")
    db.session.add(test_user)

    db.session.add_all([Scheme(id=1, name='FLS'), Scheme(id=2, name='SLS')])
    db.session.add_all([
        Grade(id=2, value='Grade 7', rank=6), Grade(id=3, value='Grade 6', rank=5),
        Grade(id=4, value='Deputy Director (SCS1)', rank=4), Grade(id=1, value='Admin Assistant (AA)', rank=7)
    ])
    db.session.add(Candidate(id=1))
    db.session.commit()

    yield session_

    transaction.rollback()
    connection.close()
    session_.remove()


@pytest.fixture
def test_candidate(test_session):
    candidate = Candidate.query.get(1)
    candidate.email_address = 'test.candidate@numberten.gov.uk'
    candidate.completed_fast_stream = True
    candidate.joining_date = date(2010, 5, 1)
    candidate.joining_grade = 1
    candidate.roles.append(Role(date_started=date(2010, 5, 1), temporary_promotion=False, grade_id=2))
    test_data = {
        'grades': [Grade(value='Band A', rank=2), Grade(value='SCS3', rank=1)],
        'test_candidates': [candidate],
    }
    for key in test_data.keys():
        test_session.add_all(test_data.get(key))
        test_session.commit()
    yield Candidate.query.first()


@pytest.fixture
def test_candidate_applied_to_fls(test_candidate, test_session):
    test_candidate.applications.append(Application(application_date=date(2019, 6, 1), scheme_id=1))
    test_session.add(test_candidate)
    test_session.commit()
    yield Candidate.query.first()


@pytest.fixture
def test_candidate_applied_and_promoted(test_candidate_applied_to_fls, test_session):
    test_candidate_applied_to_fls.roles.append(Role(date_started=date(2020, 1, 1), temporary_promotion=False))
    test_session.add(test_candidate_applied_to_fls)
    test_session.commit()
    yield


@pytest.fixture
def test_roles(test_session, test_candidate):
    roles = [Role(date_started=date(2019, 1, 1), candidate_id=test_candidate.id,
                  grade_id=Grade.query.filter(Grade.value == 'Band A').first().id)]
    test_session.add_all(roles)
    test_session.commit()
    yield


@pytest.fixture
def test_locations(test_session):
    locations = [Location(value='The North'), Location(value="The South")]
    test_session.add_all(locations)
    test_session.commit()
    yield


@pytest.fixture
def test_orgs(test_session):
    test_session.add_all([Organisation(name="Organisation 1"), Organisation(name="Organisation 2")])
    test_session.commit()
    yield


@pytest.fixture
def test_professions(test_session):
    test_session.add_all([Profession(value="Profession 1"), Profession(value="Profession 2")])
    test_session.commit()
    yield


@pytest.fixture
def test_ethnicities(test_session):
    test_session.add_all([Ethnicity(id=1, value="White British"), Ethnicity(id=2, value="Black British", bame=True)])
    test_session.commit()
    yield


@pytest.fixture
def test_multiple_candidates_multiple_ethnicities(test_session, test_ethnicities):
    test_session.add_all([Candidate(ethnicity_id=Ethnicity.query.filter_by(value="Black British").first().id) for i in range(10)])
    test_session.add_all([Candidate(ethnicity_id=Ethnicity.query.filter_by(value="White British").first().id) for i in range(10)])
    test_session.commit()
    yield


@pytest.fixture
def candidates_promoter():
    def _promoter(candidates_to_promote, decimal_ratio):
        for candidate in candidates_to_promote[0:int(len(candidates_to_promote) * decimal_ratio)]:
            candidate.roles.extend([Role(date_started=date(2019, 1, 1)), Role(date_started=date(2020, 3, 1))])
        return candidates_to_promote

    return _promoter


@pytest.fixture
def scheme_appender(test_session):
    def _add_scheme(candidates_to_add, scheme_id_to_add):
        for candidate in candidates_to_add:
            candidate.applications.append(Application(application_date=date(2019, 6, 1), scheme_id=scheme_id_to_add))
    return _add_scheme


@pytest.fixture
def logged_in_user(test_client):
    with test_client:
        test_client.post('/auth/login', data={'email-address': "Test User", 'password': 'Password'})
        yield
        test_client.get('/auth/logout')


@pytest.fixture
def seed_data(test_client):
    print("Seeding!")
    with test_client:
        clear_old_data()
        commit_data()
        yield
        print("Clearing!")
        clear_old_data()
