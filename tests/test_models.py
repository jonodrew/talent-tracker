from app.models import FLSLeadership, Leadership, Candidate, Role, Grade
from datetime import date
import pytest


def test_fls_questions_create_leadership_record(test_session):
    f = FLSLeadership(
        confident_leader=5,
        inspiring_leader=4,
        when_new_role='As soon as possible',
        confidence_built=4,
        application_id=1
    )
    test_session.add(f)
    test_session.commit()
    leadership = Leadership.query.first()
    fls = FLSLeadership.query.first()
    assert leadership.id == fls.id


class TestCandidate:
    def test_current_grade_returns_correct_grade(self, test_candidate, test_session):
        grades = Grade.query.order_by(Grade.rank.asc()).all()
        roles = [Role(date_started=date(2017 + i, 1, 1), grade=grades[i]) for i in range(3)]
        test_candidate.roles.extend(roles)
        test_session.add(test_candidate)
        test_session.commit()
        assert Candidate.query.get(test_candidate.id).current_grade().value == 'Deputy Director (SCS1)'

    @pytest.mark.parametrize(
        "list_of_role_data, expected_outcome",
        [
            (  # substantive promotion after the date
                    [
                        {'date-started': date(2019, 1, 1), 'grade-value': "Grade 7"},
                        {'date-started': date(2020, 6, 1), 'grade-value': "Grade 6", 'temporary': False}
                    ],
                    True

            ),
            (  # temporary promotion after the date
                    [
                        {'date-started': date(2019, 1, 1), 'grade-value': "Grade 7"},
                        {'date-started': date(2020, 6, 1), 'grade-value': "Grade 6", 'temporary': True}
                    ],
                    False

            ),
            (  # level transfer after the date
                    [
                        {'date-started': date(2019, 1, 1), 'grade-value': "Grade 7"},
                        {'date-started': date(2020, 6, 1), 'grade-value': "Grade 7"}
                    ],
                    False

            ),
            (  # definitely a promotion, but one that we can't take credit for
                    [
                        {'date-started': date(2019, 1, 1), 'grade-value': "Grade 7"},
                        {'date-started': date(2019, 8, 1), 'grade-value': "Grade 6", 'temporary': False}
                    ],
                    False

            ),
            (  # level transfer that we can't take credit for
                    [
                        {'date-started': date(2019, 1, 1), 'grade-value': "Grade 7"},
                        {'date-started': date(2019, 8, 1), 'grade-value': "Grade 7"}
                    ],
                    False

            ),
        ]
    )
    def test_promoted_when_started(self, list_of_role_data, expected_outcome, test_candidate, test_session):
        test_candidate.roles.extend([
            Role(date_started=list_of_role_data[0].get('date-started'),
                 grade=Grade.query.filter_by(value=list_of_role_data[0].get('grade-value')).first(),
                 temporary_promotion=False),
            Role(date_started=list_of_role_data[1].get('date-started'),
                 grade=Grade.query.filter_by(value=list_of_role_data[1].get('grade-value')).first(),
                 temporary_promotion=list_of_role_data[1].get('temporary'))
        ])
        assert test_candidate.promoted('2019-09-01') is expected_outcome

    def test_current_scheme_returns_current_scheme(self, test_candidate_applied_to_fls):
        assert test_candidate_applied_to_fls.current_scheme().name == 'FLS'


class TestGrade:
    def test_eligible_returns_correct_grades(self, test_session):
        assert ['Grade 7', 'Grade 6'] == [grade.value for grade in Grade.eligible('FLS')]
        assert ['Deputy Director (SCS1)'] == [grade.value for grade in Grade.eligible('SLS')]

    def test_new_grades_returns_correct_grades(self, test_session):
        current_grade = Grade(value='One below SCS', rank=5)
        promotion_roles = set([grade.value for grade in Grade.new_grades(current_grade)])
        assert promotion_roles == {'Grade 7', 'Grade 6', 'Deputy Director (SCS1)'}
        assert 'Admin Assistant (AA)' not in promotion_roles

    def test_new_grades_returns_grades_in_rank_order(self, test_session):
        current_grade = Grade(value='One below SCS', rank=5)
        promotion_roles = [grade.value for grade in Grade.new_grades(current_grade)]
        assert promotion_roles == ['Deputy Director (SCS1)', 'Grade 6', 'Grade 7']


class TestRole:

    @pytest.mark.parametrize("roles_values, expected_outcome", [
        (["Grade 7", "Grade 6", False], True),  # substantive promotion
        (["Grade 7", "Grade 7", True], False),  # level transfer
    ])
    def test_is_promoted_returns_correct_values(self, roles_values, expected_outcome, test_session, test_candidate):
        test_candidate.roles.extend([
                    Role(date_started=date(2019, 1, 1), grade=Grade.query.filter_by(value=roles_values[0]).first(),
                         temporary_promotion=False),
                    Role(date_started=date(2020, 6, 1), grade=Grade.query.filter_by(value=roles_values[1]).first(),
                         temporary_promotion=roles_values[2])
                ])
        assert test_candidate.roles[0].is_promotion() is expected_outcome
