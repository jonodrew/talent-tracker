from datetime import date
from app.models import Ethnicity, Scheme, Gender
from abc import ABC, abstractmethod
from io import StringIO
from werkzeug.datastructures import Headers
from flask import Response, stream_with_context
import csv


class Report(ABC):
    def __init__(self):
        self.tables = {
            'ethnicity': Ethnicity
        }
        self.filename = None
        self.headers = []
        self.filename = ''

    @abstractmethod
    def write_row(self, row_data, data_object, csv_writer):
        raise NotImplementedError

    def write_headers(self, data_object, csv_writer):
        csv_writer.writerow(self.headers)
        return data_object.getvalue()

    @staticmethod
    def decimal_or_none(first_number, second_number):
        try:
            return first_number / second_number
        except ZeroDivisionError:
            return 0

    @abstractmethod
    def get_data(self):
        raise NotImplementedError

    def generate_report_data(self):
        output = self.get_data()
        data = StringIO()
        w = csv.writer(data)

        # write header
        yield self.write_headers(data, w)
        data.seek(0)
        data.truncate(0)

        # write each item
        for item in output:
            yield self.write_row(item, data, w)
            data.seek(0)
            data.truncate(0)

    def return_data(self):
        headers = Headers()
        headers["Content-Disposition"] = f"attachment; filename={self.filename}.csv"
        headers["Content-type"] = "text/csv"

        return Response(
            stream_with_context(self.generate_report_data()),
            mimetype='text/csv', headers=headers
        )


class PromotionReport(Report, ABC):
    def __init__(self, scheme: str, year: str):
        super().__init__()
        self.scheme = Scheme.query.filter_by(name=f'{scheme}').first()
        self.promoted_before_date = date(int(year) + 1, 3, 1)  # can't take credit for promotions within first 3 months
        self.headers = ['characteristic', 'number substantively promoted', 'percentage substantively promoted',
                        'number temporarily promoted', 'percentage temporarily promoted', 'total in group']

    def write_row(self, row_data, data_object, csv_writer):
        csv_writer.writerow((
            row_data[0],
            row_data[1],
            "{0:.0%}".format(row_data[2]),  # format decimal as percentage
            row_data[3],
            "{0:.0%}".format(row_data[4]),  # format decimal as percentage
            row_data[5]
        )
        )
        return data_object.getvalue()


class CharacteristicPromotionReport(PromotionReport):
    def __init__(self, scheme: str, year: str, table_name: str):
        super().__init__(scheme, year)
        self.tables = {'ethnicity': Ethnicity, 'gender': Gender}
        self.table = self.tables.get(table_name)
        self.filename = f"promotions-by-{table_name}-{scheme}-{year}-generated-{date.today().strftime('5%d-%m-%Y')}"

    def promoted_candidates(self, characteristic, temporary):
        """
        Takes a row from one of the ProtectedCharacteristic tables (Ethnicity, WorkingPattern, etc) and returns the
        number of candidates with that characteristic who have also been promoted in the timeframe allowed by the class
        :param characteristic:
        :type characteristic:
        :param temporary:
        :type temporary:
        :return:
        :rtype:
        """
        candidates = len([candidate for candidate in characteristic.candidates
                          if candidate.promoted(self.promoted_before_date, temporary=temporary)
                          and candidate.current_scheme() == self.scheme])  # noqa
        total_candidates = len(characteristic.candidates)
        return [candidates, self.decimal_or_none(candidates, total_candidates)]

    def line_writer(self, characteristic):
        line = [f"{characteristic.value}"]
        line.extend(self.promoted_candidates(characteristic, False))
        line.extend(self.promoted_candidates(characteristic, True))
        line.append(len(characteristic.candidates))
        return line

    def get_data(self):
        output = []
        characteristics = self.table.query.all()
        for characteristic in characteristics:
            output.append(self.line_writer(characteristic))
        return output


class BooleanCharacteristicPromotionReport(CharacteristicPromotionReport):
    def get_data(self):
        return []

    def line_writer(self, characteristic):
        return []
