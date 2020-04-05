import pytest
from typing import List
from reporting.promotion_reports import (
    CharacteristicPromotionReport,
    BooleanCharacteristicPromotionReport,
    DeltaOfferPromotionReport,
)
from reporting.base_promotion_report import PromotionReport
from reporting.detailed_report import DetailedReport
from app.models import Ethnicity, Candidate, Application
from datetime import date
from freezegun import freeze_time


class TestReports:
    @pytest.mark.parametrize(
        "parameters, white_british_promoted, black_british_promoted, scheme_id, expected_output",
        [
            (
                ["FLS", 2019, "ethnicity"],
                0.5,
                0.7,
                1,
                ["White British", 5, 0.5, 0, 0.0, 10],
            ),
            (
                ["SLS", 2019, "ethnicity"],
                0.4,
                0.6,
                2,
                ["White British", 4, 0.4, 0, 0.0, 10],
            ),
        ],
    )
    @freeze_time(date(2020, 1, 1))  # we're running this report on 1 Jan 2020
    def test_reports(
        self,
        parameters: List[str],
        white_british_promoted,
        black_british_promoted,
        scheme_id,
        expected_output: str,
        test_ethnicities,
        scheme_appender,
        test_multiple_candidates_multiple_ethnicities,
        candidates_promoter,
    ):
        bb_candidates = Candidate.query.filter_by(
            ethnicity_id=Ethnicity.query.filter_by(value="Black British").first().id
        ).all()
        wb_candidates = Candidate.query.filter_by(
            ethnicity_id=Ethnicity.query.filter_by(value="White British").first().id
        ).all()
        candidates_promoter(bb_candidates, black_british_promoted)
        candidates_promoter(wb_candidates, white_british_promoted)
        scheme_appender(bb_candidates, scheme_id)
        scheme_appender(wb_candidates, scheme_id)
        output = CharacteristicPromotionReport(*parameters).get_data()
        assert output[0] == expected_output

    def test_deferred_candidates_are_not_counted(
        self, test_session, candidates_promoter
    ):
        """
        Two candidates apply to the 2019 intake and are successful. One defers to 2019. Both are promoted in the
        following year. How many "successes" should be counted for the programme? The answer should be one, because only
        one is actually on the programme at the time
        """
        test_session.add(Ethnicity(id=4, value="Prefer not to say"))
        test_session.commit()

        candidates = [Candidate(ethnicity_id=4) for i in range(2)]
        # all candidates apply for the 2019 intake and are successful
        for candidate in candidates:
            candidate.applications.append(
                Application(
                    scheme_id=1,
                    application_date=date(2018, 6, 1),
                    scheme_start_date=date(2019, 3, 1),
                    successful=True,
                )
            )
        # all candidates are substantively promoted
        candidates_promoter(candidates, 1, temporary=False)
        # one candidate defers to the 2020 intake
        candidates[0].applications[0].defer(date_to_defer_to=date(2020, 3, 1))
        # save to the database
        test_session.add_all(candidates)
        test_session.commit()

        data = CharacteristicPromotionReport("FLS", "2019", "ethnicity").get_data()
        expected_output = ["Prefer not to say", 1, 1.0, 0, 0.0, 1]
        assert data[0] == expected_output


class TestPromotionReport:
    def test_eligible_candidates(self, test_session, candidates_promoter):
        test_session.add(Ethnicity(id=4, value="Prefer not to say"))
        test_session.commit()

        candidates = [Candidate(ethnicity_id=1) for i in range(2)]
        for candidate in candidates:
            candidate.applications.append(
                Application(
                    scheme_id=1,
                    application_date=date(2018, 6, 1),
                    scheme_start_date=date(2019, 3, 1),
                )
            )
        test_session.add_all(candidates)
        candidates[0].applications[0].defer(date_to_defer_to=date(2020, 3, 1))
        test_session.commit()

        data = PromotionReport("FLS", "2019").eligible_candidates()
        assert len(data) == 1


class TestBooleanCharacteristicPromotionReport:
    def test_get_data(
        self,
        disability_with_without_no_answer,
        candidates_promoter,
        scheme_appender,
        test_session,
    ):

        candidate_groups = {
            "with_disability": Candidate.query.filter(
                Candidate.long_term_health_condition.is_(True)
            ).all(),
            "without_disability": Candidate.query.filter(
                Candidate.long_term_health_condition.is_(False)
            ).all(),
            "no_response": Candidate.query.filter(
                Candidate.long_term_health_condition.is_(None)
            ).all(),
        }

        candidates_promoter(
            candidate_groups.get("with_disability"), 0.3, temporary=False
        )
        candidates_promoter(
            candidate_groups.get("without_disability"), 0.4, temporary=False
        )
        candidates_promoter(candidate_groups.get("no_response"), 0.6, temporary=False)

        for group in candidate_groups.values():
            scheme_appender(group, scheme_id_to_add=1)

        test_session.commit()
        output = BooleanCharacteristicPromotionReport(
            "FLS", "2019", "long_term_health_condition"
        ).get_data()
        expected_output = [
            ["People with a disability", 3, 0.3, 0, 0.0, 10],
            ["People without a disability", 4, 0.4, 0, 0.0, 10],
            ["No answer provided", 6, 0.6, 0, 0.0, 10],
        ]
        assert output == expected_output


class TestDeltaOfferPromotionReport:
    def test_get_data(
        self,
        disability_with_without_no_answer,
        candidates_promoter,
        scheme_appender,
        test_session,
    ):
        candidates_with_disability = Candidate.query.filter(
            Candidate.long_term_health_condition.is_(True)
        ).all()
        delta_candidates = candidates_with_disability[0:5]
        non_delta_candidates = candidates_with_disability[5:10]

        candidates_promoter(delta_candidates, 0.8, temporary=False)
        scheme_appender(delta_candidates, delta=True)

        candidates_promoter(non_delta_candidates, 0.4, temporary=False)
        scheme_appender(non_delta_candidates)

        test_session.commit()

        output = DeltaOfferPromotionReport("FLS", "2019", "delta").get_data()
        expected_output = [
            ["Candidates eligible for DELTA", 6, 0.6, 0, 0.0, 10],
            ["Candidates on DELTA", 4, 0.8, 0, 0.0, 5],
            ["Candidates not on DELTA", 2, 0.4, 0, 0.0, 5],
        ]
        assert expected_output == output


class TestDetailedPromotionReport:
    @pytest.mark.parametrize("intake_year", (2018, 2019, 2020))
    @pytest.mark.parametrize("role_change_type", (1, 2, 3))
    @freeze_time(date(2020, 3, 1))
    def test_get_data(
        self,
        role_change_type,
        test_candidate_applied_and_promoted,
        intake_year,
        test_session,
    ):
        report = DetailedReport(intake_year, "FLS", role_change_type)
        if (
            intake_year == 2019 and role_change_type == 2
        ):  # 2 is a substantive promotion
            assert report.get_data()[0] == [
                "Testy Candidate",
                "test.candidate@numberten.gov.uk",
                "test.secondary@gov.uk",
                1,
                "META",
                "Director of Happiness",
                "Director (SCS2)",
                "Stargate-1",
                "Department of Fun",
                date(2017, 9, 1),
                "Admin Assistant (AA)",
                True,
                "Terran",
                True,
                True,
                True,
                "Fork",
                "Pan",
                True,
                "Immortal",
                "Don't forget to be awesome",
                "24/7",
                "localhost:5000/candidates/candidate/1",
            ]
        else:
            assert report.get_data() == []
