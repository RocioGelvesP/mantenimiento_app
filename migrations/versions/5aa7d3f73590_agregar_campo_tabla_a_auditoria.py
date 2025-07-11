"""Agregar campo tabla a auditoria

Revision ID: 5aa7d3f73590
Revises: ff75e5cfcea3
Create Date: 2025-07-07 17:30:49.836879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5aa7d3f73590'
down_revision = 'ff75e5cfcea3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('auditoria', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tabla', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('auditoria', schema=None) as batch_op:
        batch_op.drop_column('tabla')

    # ### end Alembic commands ###
