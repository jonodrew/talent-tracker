from datetime import date
from typing import List
from sqlalchemy import and_

from app.models import (
    Ethnicity,
    Scheme,
    Gender,
    Candidate,
    Application,
    Sexuality,
    WorkingPattern,
    Belief,
    AgeRange,
)
from abc import ABC, abstractmethod
from io import StringIO
from werkzeug.datastructures import Headers
from flask import Response, stream_with_context
import csv


class Report(ABC):
    def __init__(self):
        self.tables = {"ethnicity": Ethnicity}
        self.filename = None
        self.headers = []
        self.filename = ""

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
            mimetype="text/csv",
            headers=headers,
        )


class PromotionReport(Report, ABC):
    def __init__(self, scheme: str, year: str, attribute: str = None):
        super().__init__()
        self.attribute = attribute
        self.intake_date = date(
            int(year), 3, 1
        )  # assuming it starts in March every year
        self.scheme = Scheme.query.filter_by(name=f"{scheme}").first()
        self.promoted_before_date = date(
            int(year) + 1, 3, 1
        )  # can't take credit for promotions within first 3 months
        self.headers = [
            "characteristic",
            "number substantively promoted",
            "percentage substantively promoted",
            "number temporarily promoted",
            "percentage temporarily promoted",
            "total in group",
        ]
        self.filename = f"promotions-by-{attribute}-{scheme}-{year}-generated-{date.today().strftime('5%d-%m-%Y')}"

    def get_data(self):
        output = []
        for tupl in self.get_row_metadata():
            output.append(self.row_writer(tupl[0], tupl[1]))
        return output

    def row_writer(self, row_header, candidate_list):
        output = [row_header]
        output.extend(self.chunk_writer(False, candidate_list))
        output.extend(self.chunk_writer(True, candidate_list))
        output.append(len(candidate_list))
        return output

    def chunk_writer(self, temporary, candidates):
        promoted_number = len(self.promoted_candidates(temporary, candidates))
        return [promoted_number, self.decimal_or_none(promoted_number, len(candidates))]

    def eligible_candidates(self) -> List[Candidate]:
        """
        Candidates eligible to be reported on have an application whose scheme start date is aligned with ```year``` and
        whose Application -> Scheme -> name is the same as ```scheme```. For example, the 2019 FLS intake all have a
        scheme_start_date on their applications of 2019/03/01 and a scheme_id that references the 'FLS' scheme.
        :return:
        :rtype:
        """
        eligible_applications = Application.query.filter(
            and_(
                Application.scheme_start_date == self.intake_date,
                Application.scheme_id == self.scheme.id,
            )
        ).all()
        return [application.candidate for application in eligible_applications]

    def promoted_candidates(self, temporary, candidates: List[Candidate]):
        return [
            candidate
            for candidate in candidates
            if candidate.promoted_between(self.promoted_before_date, temporary)
        ]

    def write_row(self, row_data, data_object, csv_writer):
        csv_writer.writerow(
            (
                row_data[0],
                row_data[1],
                "{0:.0%}".format(row_data[2]),  # format decimal as percentage
                row_data[3],
                "{0:.0%}".format(row_data[4]),  # format decimal as percentage
                row_data[5],
            )
        )
        return data_object.getvalue()


class CharacteristicPromotionReport(PromotionReport):
    def __init__(self, scheme: str, year: str, attribute: str):
        super().__init__(scheme, year, attribute)
        self.tables = {
            "ethnicity": Ethnicity,
            "gender": Gender,
            "sexuality": Sexuality,
            "belief": Belief,
            "working_pattern": WorkingPattern,
            "age_range": AgeRange,
        }
        self.table = self.tables.get(self.attribute)

    def get_row_metadata(self):
        return [
            (row.value, self.candidates_with_characteristic(row))
            for row in self.table.query.all()
        ]

    def candidates_with_characteristic(self, characteristic):
        return [
            candidate
            for candidate in self.eligible_candidates()
            if getattr(candidate, self.attribute) == characteristic
        ]


class BooleanCharacteristicPromotionReport(PromotionReport):
    def __init__(self, scheme: str, year: str, attribute: str):
        super().__init__(scheme, year, attribute)
        self.human_readable_characteristics = {
            "long_term_health_condition": {
                True: "People with a disability",
                False: "People without a disability",
                None: "No answer provided",
            },
            "caring_responsibility": {
                True: "I have caring responsibilities",
                False: "I do not have caring responsibilities",
                None: "No answer provided",
            },
        }
        self.human_readable_row_titles = self.human_readable_characteristics.get(
            self.attribute
        )

    def get_row_metadata(self):
        return [
            (
                value,
                Candidate.query.filter(
                    getattr(Candidate, self.attribute).is_(key)
                ).all(),
            )
            for key, value in self.human_readable_row_titles.items()
        ]


class OfferPromotionReport(PromotionReport):
    def __init__(self, scheme, year, attribute):
        super().__init__(scheme, year, attribute)
        self.upper_attribute = attribute.upper()
        self.human_readable_row_titles = {
            True: f"Candidates eligible for {self.upper_attribute}",
            False: f"Candidates on {self.upper_attribute}",
        }

    def get_row_metadata(self):
        return [
            (
                f"Candidates eligible for {self.upper_attribute}",
                self.eligible_candidates(),
            ),
            (
                f"Candidates on {self.upper_attribute}",
                self.candidates_on_offer(self.attribute),
            ),
            (
                f"Candidates not on {self.upper_attribute}",
                list(
                    set(self.eligible_candidates())
                    - set(self.candidates_on_offer(self.attribute))
                ),
            ),
        ]

    def candidates_on_offer(self, offer):
        return [
            candidate
            for candidate in super().eligible_candidates()
            if getattr(candidate.applications[0], offer)
        ]


class MetaOfferPromotionReport(OfferPromotionReport):
    def __init__(self, scheme, year, attribute):
        super().__init__(scheme, year, attribute)

    def eligible_candidates(self):
        return [
            candidate
            for candidate in super().eligible_candidates()
            if candidate.ethnicity.bame
        ]


class DeltaOfferPromotionReport(OfferPromotionReport):
    def __init__(self, scheme, year, attribute):
        super().__init__(scheme, year, attribute)

    def eligible_candidates(self):
        return [
            candidate
            for candidate in super().eligible_candidates()
            if candidate.long_term_health_condition
        ]


class DetailedPromotionReport(Report):
    def __init__(self, promoted, start_date, end_date):
        super().__init__()
        pass

    def get_data(self):
        return [[], []]

    def write_headers(self, data_object, csv_writer):
        pass

    def write_row(self, row_data, data_object, csv_writer):
        pass
