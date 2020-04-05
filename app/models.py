from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from flask_migrate import Migrate
from flask_login import LoginManager
from datetime import datetime
from sqlalchemy import and_, func
from sqlalchemy.ext.declarative import declared_attr


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


class CandidateGetterMixin:
    @declared_attr
    def candidates(cls):
        try:
            backref = cls.__table_name__
        except AttributeError:
            backref = cls.__name__.lower()
        return db.relationship("Candidate", backref=backref)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def check_password(self, password_to_check: str) -> bool:
        return check_password_hash(self.password_hash, password_to_check)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def __repr__(self):
        return "<User {}>".format(self.email)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Ethnicity(CandidateGetterMixin, db.Model):
    """
    The ethnicity table has a boolean flag for bame, allowing us to query candidates (and therefore data connected to
    candidates) according to ethnicity at a broad, BAME level
    """

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(512))
    bame = db.Column(db.Boolean)


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    joining_date = db.Column(db.Date())
    completed_fast_stream = db.Column(db.Boolean())
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    email_address = db.Column(db.String(120), unique=True)
    secondary_email_address = db.Column(db.String(120), unique=True)

    # protected characteristics
    caring_responsibility = db.Column(
        db.Boolean()
    )  # TRUE: yes, FALSE: no, NULL: Prefer not to say
    long_term_health_condition = db.Column(db.Boolean())

    age_range_id = db.Column(db.ForeignKey("age_range.id"), nullable=False, default=1)
    working_pattern_id = db.Column(db.ForeignKey("working_pattern.id"))
    belief_id = db.Column(db.ForeignKey("belief.id"))
    sexuality_id = db.Column(db.ForeignKey("sexuality.id"))
    gender_id = db.Column(db.ForeignKey("gender.id"))
    ethnicity_id = db.Column(db.ForeignKey("ethnicity.id"))
    main_job_type_id = db.Column(db.ForeignKey("main_job_type.id"))
    joining_grade_id = db.Column(db.ForeignKey("grade.id"))

    roles = db.relationship(
        "Role", backref="candidate", lazy="dynamic", order_by="Role.date_started.desc()"
    )
    applications = db.relationship(
        "Application",
        backref="candidate",
        lazy="dynamic",
        order_by="Application.scheme_start_date.desc()",
    )
    joining_grade = db.relationship("Grade", backref="candidate")
    role_changes = db.relationship("RoleChangeEvent", backref="candidate")

    def __repr__(self):
        return f"<Candidate email {self.email_address}>"

    def current_grade(self) -> "Grade":
        return self.roles.order_by(Role.date_started.desc()).first().grade

    def promoted(
        self,
        promoted_after_date: datetime.date,
        promoted_before_date=None,
        temporary=False,
    ):
        """
        Returns whether this candidate was promoted after the passed date. Promotions are only considered if they're
        substantive. There is a flag is users want to see temporary promotions instead
        :param promoted_after_date:
        :type promoted_after_date:
        :param temporary: Whether the user wants temporary or substantive promotions
        :type temporary: bool
        :return:
        :rtype:
        """
        if temporary:
            role_change = Promotion.query.filter(
                Promotion.value.like("%temporary%")
            ).first()
        else:
            role_change = Promotion.query.filter(
                Promotion.value.like("%substantive%")
            ).first()
        if not promoted_before_date:
            promoted_before_date = datetime.today()
        roles_after_date = self.roles.filter(
            and_(
                Role.date_started >= promoted_after_date,
                Role.date_started <= promoted_before_date,
                Role.role_change == role_change,
            )
        ).all()
        return len(roles_after_date) > 0

    def current_scheme(self) -> "Scheme":
        return Scheme.query.get(
            self.applications.order_by(Application.application_date.desc())
            .first()
            .scheme_id
        )

    def most_recent_application(self) -> "Application":
        return (
            Application.query.filter(Application.candidate_id == self.id)
            .order_by(Application.application_date.desc())
            .first()
        )

    def current_location(self):
        return self.roles.order_by(Role.id.desc()).first().location.value

    def roles_since_date(self, since_date: datetime.date):
        return [role for role in self.roles if role.date_started >= since_date]

    def update_email(self, new_address: str, primary: bool):
        if primary:
            self.email_address = new_address
        elif not primary:
            self.secondary_email_address = new_address

    def new_role(
        self,
        start_date: datetime.date,
        new_org_id,
        new_profession_id,
        new_location_id,
        new_grade_id,
        new_title,
        role_change_id,
    ):
        self.roles.append(
            Role(
                date_started=start_date,
                organisation_id=new_org_id,
                profession_id=new_profession_id,
                location_id=new_location_id,
                grade_id=new_grade_id,
                role_name=new_title,
                role_change_id=role_change_id,
            )
        )
        self.role_changes.append(
            RoleChangeEvent(
                candidate_id=self.id,
                former_role_id=self.roles[1].id,
                new_role_id=self.roles[0].id,
                role_change_id=role_change_id,
                role_change_date=start_date,
            )
        )


class Organisation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True, unique=True)
    parent_organisation_id = db.Column(db.ForeignKey("organisation.id"), unique=False)
    department = db.Column(db.Boolean())
    arms_length_body = db.Column(db.Boolean())

    roles = db.relationship("Role", backref="organisation", lazy="dynamic")

    def __repr__(self):
        return f"<Org {self.name}>"


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(100))
    rank = db.Column(db.Integer, nullable=False)

    @staticmethod
    def eligible(scheme: str):
        """
        This method returns those Grades that are eligible for specific schemes.
        :param scheme: name of the scheme
        :type scheme: str
        :return: A list of eligible Grades
        :rtype: List[Grade]
        """
        if scheme == "FLS":
            eligible_grades = Grade.query.filter(Grade.value.like("Grade%")).all()
        else:
            eligible_grades = Grade.query.filter(Grade.value.like("Deputy%"))
        return eligible_grades

    @staticmethod
    def new_grades(current_grade: "Grade"):
        """
        Grades that are one below, equal to, or more senior than, `current_grade`. We include grades one below because
        candidates may be coming off temporary promotion. Remember that the more senior the role, the lower the rank
        value!
        :param current_grade: Grade object, describing the current Grade of Candidate
        :type current_grade: Grade
        :return: A list of grades more senior or at the same level
        :rtype: List[Grade]
        """
        current_rank = current_grade.rank
        return (
            Grade.query.filter(Grade.rank <= (current_rank + 1))
            .order_by(Grade.rank.asc())
            .all()
        )

    def __repr__(self):
        return f"Grade {self.value}"


class Profession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(256))


class Location(db.Model):
    """
    The location_tag value is for one of four values: London, Region, Overseas, or Devolved. This allows for easier
    data retrieval when searching for promotions or applications from a broad space
    """

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(128))
    location_tag = db.Column(db.String(16), index=True)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_started = db.Column(db.Date())
    role_name = db.Column(db.String(256))

    organisation_id = db.Column(db.ForeignKey("organisation.id"))
    candidate_id = db.Column(db.ForeignKey("candidate.id"))
    profession_id = db.Column(db.ForeignKey("profession.id"))
    location_id = db.Column(db.ForeignKey("location.id"))
    grade_id = db.Column(db.ForeignKey("grade.id"))
    role_change_id = db.Column(db.ForeignKey("promotion.id"))

    grade = db.relationship("Grade", lazy="select")
    location = db.relationship("Location", lazy="select")
    profession = db.relationship("Profession", lazy="select")
    role_change = db.relationship("Promotion", lazy="select")

    def __repr__(self):
        return f"<Role held by {self.candidate} at {self.organisation_id}>"

    def is_promotion(self):
        role_before_this = (
            self.candidate.roles.order_by(Role.date_started.desc()).limit(2).all()[1]
        )
        return self.grade.rank < role_before_this.grade.rank


class Scheme(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(16))


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    aspirational_grade_id = db.Column(db.ForeignKey("grade.id"))
    scheme_id = db.Column(db.ForeignKey("scheme.id"))
    candidate_id = db.Column(db.ForeignKey("candidate.id"), nullable=False)

    application_date = db.Column(db.Date())
    scheme_start_date = db.Column(db.Date(), index=True)
    per_id = db.Column(db.Integer())
    employee_number = db.Column(db.String(25))
    successful = db.Column(db.Boolean())
    meta = db.Column(db.Boolean, default=False)
    delta = db.Column(db.Boolean, default=False)
    cohort = db.Column(db.Integer, unique=False)
    withdrawn = db.Column(db.Boolean(), default=False)

    aspirational_grade = db.relationship("Grade", lazy="select")

    def defer(self, date_to_defer_to: datetime.date):
        self.scheme_start_date = date_to_defer_to
        return None

    def offer_status(self):
        if self.delta:
            output = "DELTA"
        elif self.meta:
            output = "META"
        elif self.meta and self.delta:
            output = "META and DELTA"
        else:
            output = None
        return output


class Leadership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    confident_leader = db.Column(db.Integer())
    inspiring_leader = db.Column(db.Integer())
    when_new_role = db.Column(db.String(256))
    confidence_built = db.Column(db.Integer())

    application_id = db.Column(db.ForeignKey("application.id"), nullable=False)

    type = db.Column(db.String(50))

    __mapper_args__ = {"polymorphic_identity": "leadership", "polymorphic_on": type}


class FLSLeadership(Leadership):
    id = db.Column(db.Integer(), db.ForeignKey("leadership.id"), primary_key=True)
    increased_visibility = db.Column(db.Integer())

    __mapper_args__ = {"polymorphic_identity": "fls_leadership"}


class SLSLeadership(Leadership):
    id = db.Column(db.Integer(), db.ForeignKey("leadership.id"), primary_key=True)
    work_differently = db.Column(db.Integer())
    using_tools = db.Column(db.Integer())
    feel_ready = db.Column(db.Integer())

    __mapper_args__ = {"polymorphic_identity": "sls_leadership"}


class MainJobType(CandidateGetterMixin, db.Model):
    __table_name__ = "main_job_type"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(512))
    lower_socio_economic_background = db.Column(db.Boolean, default=False)


class AgeRange(CandidateGetterMixin, db.Model):
    __table_name__ = "age_range"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(10))


class WorkingPattern(CandidateGetterMixin, db.Model):
    __table_name__ = "working_pattern"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(128))


class Belief(CandidateGetterMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(128))


class Gender(CandidateGetterMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(128))


class Sexuality(CandidateGetterMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(128))


class AuditEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)
    action_taken = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=func.now())


class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(28), index=True)


class RoleChangeEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_change_date = db.Column(db.Date())

    candidate_id = db.Column(db.ForeignKey("candidate.id"))
    former_role_id = db.Column(db.ForeignKey("role.id"))
    new_role_id = db.Column(db.ForeignKey("role.id"))
    role_change_id = db.Column(db.ForeignKey("promotion.id"))
