"""Add role name to Role

Revision ID: f61d93b55701
Revises: eb885b326420
Create Date: 2019-07-01 18:09:01.963123

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f61d93b55701"
down_revision = "eb885b326420"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("role", sa.Column("role_name", sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("role", "role_name")
    # ### end Alembic commands ###
