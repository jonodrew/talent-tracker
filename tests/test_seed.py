from modules.seed import SeedData
from app.models import Ethnicity, Grade
import pytest


@pytest.mark.parametrize(
    "spreadsheet_data_tuple, count",
    [(("Ethnicity", Ethnicity), 19), (("Grade", Grade), 13)],
)
class TestSeedData:
    def test_ethnicity_process(self, spreadsheet_data_tuple, count, test_session):
        sd = SeedData(
            "/Users/jonathankerr/projects/talent-tracker/data/database-content.xlsx"
        )
        out = sd._process_from_spreadsheet(spreadsheet_data_tuple)
        assert type(out) is list
        assert len(out) == count

    def test_commit(self, spreadsheet_data_tuple, count, test_session):
        sd = SeedData(
            "/Users/jonathankerr/projects/talent-tracker/data/database-content.xlsx"
        )
        sd.sheets_to_upload = [spreadsheet_data_tuple]
        spreadsheet_data_tuple[1].query.delete()
        test_session.commit()
        sd.seed_data()
        assert len(spreadsheet_data_tuple[1].query.all()) == count
