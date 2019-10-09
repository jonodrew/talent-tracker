from app.models import Ethnicity, Candidate, Organisation, Profession, Grade
from modules.seed import clear_old_data
import pytest


@pytest.mark.parametrize(
    "spreadsheet_data_tuple, count",
    [(("Ethnicity", Ethnicity), 19), (("Grade", Grade), 13)],
)
class TestSeedData:
    def test_ethnicity_process(
        self, spreadsheet_data_tuple, count, test_session, class_seed_data
    ):
        sd = class_seed_data
        out = sd._process_from_spreadsheet(spreadsheet_data_tuple)
        assert type(out) is list
        assert len(out) == count

    def test_commit(self, spreadsheet_data_tuple, count, test_session, class_seed_data):
        sd = class_seed_data
        sd.sheets_to_upload = [spreadsheet_data_tuple]
        spreadsheet_data_tuple[1].query.delete()
        test_session.commit()
        sd.seed_data()
        assert len(spreadsheet_data_tuple[1].query.all()) == count


class TestSeedScript:
    def test_commit_data(self, seed_data):
        for item in [
            (Candidate, 201),
            (Organisation, 2),
            (Grade, 13),
            (Profession, 27),
        ]:
            assert len(item[0].query.all()) == item[1]

    @pytest.mark.parametrize("model", [Candidate, Organisation, Grade, Profession])
    def test_clear_old_data(self, model, test_session, test_client):
        with test_client:
            clear_old_data()
            for model in [Candidate, Organisation, Grade, Profession]:
                assert 0 == len(model.query.all())
