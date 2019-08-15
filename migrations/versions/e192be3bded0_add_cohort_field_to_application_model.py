"""Add cohort field to Application model

Revision ID: e192be3bded0
Revises: 0bcdc20a2c99
Create Date: 2019-06-10 09:46:50.090652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e192be3bded0"
down_revision = "0bcdc20a2c99"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("application", sa.Column("cohort", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("application", "cohort")
    # ### end Alembic commands ###
