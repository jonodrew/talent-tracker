"""Remove Role.temporary_promotion

Revision ID: 33a9387b9fe3
Revises: 496431eda64c
Create Date: 2019-07-09 16:20:51.050349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "33a9387b9fe3"
down_revision = "496431eda64c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("role", "temporary_promotion")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "role",
        sa.Column(
            "temporary_promotion", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    # ### end Alembic commands ###
