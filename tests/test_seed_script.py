from modules.seed import commit_data, clear_old_data
from app.models import Candidate, Organisation, Profession, Grade
import pytest


@pytest.mark.parametrize("model, count", [
    (Candidate, 2), (Organisation, 45), (Grade, 17), (Profession, 15)
])
# the extra candidates and grades come from loading the data in at db creation time
def test_commit_data(model, count, test_session):
    commit_data()
    assert count == len(model.query.all())


@pytest.mark.parametrize("model", [Candidate, Organisation, Grade, Profession])
def test_clear_old_data(model, test_session, test_client):
    with test_client:
        clear_old_data()
        for model in [Candidate, Organisation, Grade, Profession]:
            assert 0 == len(model.query.all())
