"""Add income earner employee status - a table for answers to a question about the status of the main income earner in
Candidate's household while they were growing up

Revision ID: afeb7681096b
Revises: 941671d6346a
Create Date: 2019-05-21 16:14:18.885415

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "afeb7681096b"
down_revision = "941671d6346a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "income_earner_employee_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("value", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.drop_column("changeable_protected_characteristics", "sexuality")
    op.drop_column("changeable_protected_characteristics", "gender")
    op.drop_column("socio_economic", "income_earner_employee")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "socio_economic",
        sa.Column(
            "income_earner_employee", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "changeable_protected_characteristics",
        sa.Column("gender", sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    )
    op.add_column(
        "changeable_protected_characteristics",
        sa.Column(
            "sexuality", sa.VARCHAR(length=128), autoincrement=False, nullable=True
        ),
    )
    op.drop_table("income_earner_employee_status")
    # ### end Alembic commands ###
