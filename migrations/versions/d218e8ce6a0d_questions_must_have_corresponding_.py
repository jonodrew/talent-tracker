"""Questions must have corresponding Application

Revision ID: d218e8ce6a0d
Revises: bf7f2303b52b
Create Date: 2019-05-10 11:04:35.552412

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d218e8ce6a0d"
down_revision = "bf7f2303b52b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "leadership", "application_id", existing_type=sa.INTEGER(), nullable=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "leadership", "application_id", existing_type=sa.INTEGER(), nullable=True
    )
    # ### end Alembic commands ###
