from modules import upload
import os

class TestUpload:

    def test_create_candidate_data(self):
        directory = os.path.dirname(__file__)
        filename = os.path.join(directory, 'data/test_csv.csv')
        u = upload.Upload(filename, 'FLS', '3/3/2020')
        c = u.create_candidate_data_row(u.file_content[0])
        assert c
