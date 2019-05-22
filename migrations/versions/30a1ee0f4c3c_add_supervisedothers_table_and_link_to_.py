"""Add SupervisedOthers table and link to SocioEconomic

Revision ID: 30a1ee0f4c3c
Revises: afeb7681096b
Create Date: 2019-05-21 16:18:38.223267

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30a1ee0f4c3c'
down_revision = 'afeb7681096b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('supervised_others',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('value', sa.String(length=512), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('socio_economic', sa.Column('supervised_others_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'socio_economic', 'supervised_others', ['supervised_others_id'], ['id'])
    op.drop_column('socio_economic', 'supervisor')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('socio_economic', sa.Column('supervisor', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'socio_economic', type_='foreignkey')
    op.drop_column('socio_economic', 'supervised_others_id')
    op.drop_table('supervised_others')
    # ### end Alembic commands ###
