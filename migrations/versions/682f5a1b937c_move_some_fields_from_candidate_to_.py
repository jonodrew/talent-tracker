"""Move some fields from Candidate to Application

Revision ID: 682f5a1b937c
Revises: f195b7cb6a18
Create Date: 2019-05-10 09:30:04.840911

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "682f5a1b937c"
down_revision = "f195b7cb6a18"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "application", sa.Column("scheme_start_date", sa.Date(), nullable=True)
    )
    op.create_index(
        op.f("ix_application_scheme_start_date"),
        "application",
        ["scheme_start_date"],
        unique=False,
    )
    op.drop_column("candidate", "scheme")
    op.drop_column("candidate", "scheme_start_date")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "candidate",
        sa.Column("scheme_start_date", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "candidate",
        sa.Column("scheme", sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    )
    op.drop_index(op.f("ix_application_scheme_start_date"), table_name="application")
    op.drop_column("application", "scheme_start_date")
    # ### end Alembic commands ###
