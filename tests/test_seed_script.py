from modules.seed import clear_old_data
from app.models import Candidate, Organisation, Profession, Grade
import pytest


def test_commit_data(seed_data):
    for item in [(Candidate, 201), (Organisation, 408), (Grade, 13), (Profession, 27)]:
        assert len(item[0].query.all()) == item[1]


@pytest.mark.parametrize("model", [Candidate, Organisation, Grade, Profession])
def test_clear_old_data(model, test_session, test_client):
    with test_client:
        clear_old_data()
        for model in [Candidate, Organisation, Grade, Profession]:
            assert 0 == len(model.query.all())
