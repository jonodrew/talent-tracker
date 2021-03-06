"""Add temporary promotion boolean on Role

Revision ID: 34851186e7a6
Revises: eadbcbde0556
Create Date: 2019-06-03 15:23:53.948768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "34851186e7a6"
down_revision = "eadbcbde0556"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "role",
        sa.Column("temporary_promotion", sa.Boolean(), nullable=True, default=False),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("role", "temporary_promotion")
    # ### end Alembic commands ###
