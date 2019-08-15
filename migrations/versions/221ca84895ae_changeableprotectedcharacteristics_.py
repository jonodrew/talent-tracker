"""ChangeableProtectedCharacteristics belong to Candidate now

Revision ID: 221ca84895ae
Revises: 4545f69ecd58
Create Date: 2019-06-19 13:17:17.294702

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "221ca84895ae"
down_revision = "4545f69ecd58"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "application_changeable_protected_characteristics_fkey",
        "application",
        type_="foreignkey",
    )
    op.drop_column("application", "changeable_protected_characteristics")
    op.add_column(
        "candidate",
        sa.Column("changeable_protected_characteristics", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        None,
        "candidate",
        "changeable_protected_characteristics",
        ["changeable_protected_characteristics"],
        ["id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "candidate_changeable_protected_characteristics_fkey",
        "candidate",
        type_="foreignkey",
    )
    op.drop_column("candidate", "changeable_protected_characteristics")
    op.add_column(
        "application",
        sa.Column(
            "changeable_protected_characteristics",
            sa.INTEGER(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "application_changeable_protected_characteristics_fkey",
        "application",
        "changeable_protected_characteristics",
        ["changeable_protected_characteristics"],
        ["id"],
    )
    # ### end Alembic commands ###
