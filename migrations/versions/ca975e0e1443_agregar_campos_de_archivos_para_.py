"""Agregar campos de archivos para instructivos, estándar de seguridad, operación, mecánico, eléctrico y partes

Revision ID: ca975e0e1443
Revises: 3618e6089566
Create Date: 2025-06-17 12:14:38.844778

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca975e0e1443'
down_revision = '3618e6089566'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('equipos', schema=None) as batch_op:
        # batch_op.add_column(sa.Column('instructivos_link', sa.String(length=255), nullable=True))
        # batch_op.add_column(sa.Column('estandar_seguridad_link', sa.String(length=255), nullable=True))
        # batch_op.add_column(sa.Column('instructivos_file', sa.String(length=255), nullable=True))
        # batch_op.add_column(sa.Column('estandar_seguridad_file', sa.String(length=255), nullable=True))
        # batch_op.add_column(sa.Column('operacion_file', sa.String(length=255), nullable=True))
        # batch_op.add_column(sa.Column('mecanico_file', sa.String(length=255), nullable=True))
        # batch_op.add_column(sa.Column('electrico_file', sa.String(length=255), nullable=True))
        # batch_op.add_column(sa.Column('partes_file', sa.String(length=255), nullable=True))
        pass

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('equipos', schema=None) as batch_op:
        batch_op.drop_column('partes_file')
        batch_op.drop_column('electrico_file')
        batch_op.drop_column('mecanico_file')
        batch_op.drop_column('operacion_file')
        batch_op.drop_column('estandar_seguridad_file')
        batch_op.drop_column('instructivos_file')
        batch_op.drop_column('estandar_seguridad_link')
        batch_op.drop_column('instructivos_link')

    # ### end Alembic commands ###
