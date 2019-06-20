"""ProtectedCharacteristics renamed and moved to extend Candidate class

Revision ID: 5f7addaabfa5
Revises: 32f494d61331
Create Date: 2019-06-20 09:57:39.831859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f7addaabfa5'
down_revision = '32f494d61331'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('changeable_protected_characteristics', 'protected_characteristics')
    op.add_column('candidate', sa.Column('type', sa.String(length=50), nullable=True))
    op.drop_constraint('candidate_ethnicity_id_fkey', 'candidate', type_='foreignkey')
    op.drop_constraint('candidate_changeable_protected_characteristics_id_fkey', 'candidate', type_='foreignkey')
    op.drop_column('candidate', 'ethnicity_id')
    op.drop_column('candidate', 'changeable_protected_characteristics_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('protected_characteristics', 'changeable_protected_characteristics')
    op.add_column('candidate', sa.Column('changeable_protected_characteristics_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('candidate', sa.Column('ethnicity_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('candidate_changeable_protected_characteristics_id_fkey', 'candidate', 'changeable_protected_characteristics', ['changeable_protected_characteristics_id'], ['id'])
    op.create_foreign_key('candidate_ethnicity_id_fkey', 'candidate', 'ethnicity', ['ethnicity_id'], ['id'])
    op.drop_column('candidate', 'type')
    # ### end Alembic commands ###
