from app.models import FLSLeadership, Application, Leadership, Candidate, Role, Grade
from datetime import date
import pytest


def test_fls_questions_create_leadership_record(test_database):
    f = FLSLeadership(
        confident_leader=5,
        inspiring_leader=4,
        when_new_role='As soon as possible',
        confidence_built=4,
        application_id=1
    )
    test_database.session.add(f)
    test_database.session.commit()
    leadership = Leadership.query.first()
    fls = FLSLeadership.query.first()
    assert leadership.id == fls.id


class TestCandidate:
    def test_candidate_cannot_apply_without_role(self, test_candidate):
        with pytest.raises(AssertionError):
            Application(
                aspirational_grade=2,
                scheme_id=1,
                application_date=date(2018, 6, 1),
                scheme_start_date=date(2019, 9, 1),
                per_id=1,
                employee_number='cab10101010',
                candidate_id=1,
            )

    def test_current_grade_returns_correct_grade(self, test_candidate, test_database, test_grades):
        grades = Grade.query.order_by(Grade.rank.asc()).all()
        test_database.session.add_all(
            [
                Role(date_started=date(2017, 1, 1), candidate_id=test_candidate.id, grade=grades[0]),
                Role(date_started=date(2018, 1, 1), candidate_id=test_candidate.id, grade=grades[1]),
                Role(date_started=date(2019, 1, 1), candidate_id=test_candidate.id, grade=grades[2])
            ]
        )
        test_database.session.commit()
        assert Candidate.query.get(test_candidate.id).current_grade().value == 'Deputy Director (SCS1)'

    def test_promoted_when_started(self, test_candidate, test_database, test_grades):
        grades = Grade.query.order_by(Grade.rank.asc()).all()
        test_candidate.roles = [
            Role(date_started=date(2019, 1, 1), candidate_id=test_candidate.id, grade=grades[0]),
            Role(date_started=date(2020, 6, 1), candidate_id=test_candidate.id, grade=grades[-1])
        ]
        test_database.session.add(test_candidate)
        assert test_candidate.promoted('2019-09-01')


class TestGrade:
    def test_eligible_returns_correct_grades(self, test_database, test_grades):
        assert ['Grade 7', 'Grade 6'] == [grade.value for grade in Grade.eligible('FLS')]
        assert ['Deputy Director (SCS1)'] == [grade.value for grade in Grade.eligible('SLS')]

    def test_new_grades_returns_correct_grades(self, test_database, test_grades):
        current_grade = Grade(value='One below SCS', rank=5)
        promotion_roles = set([grade.value for grade in Grade.new_grades(current_grade)])
        assert promotion_roles == {'Grade 7', 'Grade 6', 'Deputy Director (SCS1)'}
        assert 'Admin Assistant (AA)' not in promotion_roles

    def test_new_grades_returns_grades_in_rank_order(self, test_database, test_grades):
        current_grade = Grade(value='One below SCS', rank=5)
        promotion_roles = [grade.value for grade in Grade.new_grades(current_grade)]
        assert promotion_roles == ['Deputy Director (SCS1)', 'Grade 6', 'Grade 7']
