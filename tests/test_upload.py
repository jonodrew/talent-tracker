from modules.upload import Upload
import os
from app.models import Candidate, Organisation


class TestUpload:
    def test_create_candidate_data(self, test_session):
        test_session.add(Organisation(name="Foreign and Commonwealth Office"))
        test_session.commit()
        directory = os.path.dirname(__file__)
        filename = os.path.join(directory, "data/test_csv.csv")
        u = Upload(filename, "FLS", "2020-3-3")
        u.complete_upload()
        candidate = Candidate.query.filter_by(first_name="James").first()
        assert candidate
        assert len(candidate.applications.all()) == 1
        assert len(candidate.roles.all()) == 1
