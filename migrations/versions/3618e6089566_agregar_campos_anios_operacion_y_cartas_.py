"""Agregar campos anios_operacion y cartas_lubricacion a Equipo

Revision ID: 3618e6089566
Revises: c06f60e1f70e
Create Date: 2025-06-17 11:34:52.762000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3618e6089566'
down_revision = 'c06f60e1f70e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('equipos', schema=None) as batch_op:
        # batch_op.add_column(sa.Column('anios_operacion', sa.String(length=20), nullable=True))
        # batch_op.add_column(sa.Column('cartas_lubricacion', sa.String(length=20), nullable=True))
        pass

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('equipos', schema=None) as batch_op:
        batch_op.drop_column('cartas_lubricacion')
        batch_op.drop_column('anios_operacion')

    # ### end Alembic commands ###
