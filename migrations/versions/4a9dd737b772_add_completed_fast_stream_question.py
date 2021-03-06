"""Add completed Fast Stream question

Revision ID: 4a9dd737b772
Revises: 266a2516befd
Create Date: 2019-05-21 12:11:31.649763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4a9dd737b772"
down_revision = "266a2516befd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "candidate", sa.Column("completed_fast_stream", sa.Boolean(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("candidate", "completed_fast_stream")
    # ### end Alembic commands ###
