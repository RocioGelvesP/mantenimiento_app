"""agregar campo imagen_lubricacion a equipo

Revision ID: 989edf4ee0dd
Revises: 250c3bd026e2
Create Date: 2025-06-21 13:36:53.155649

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '989edf4ee0dd'
down_revision = '250c3bd026e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # with op.batch_alter_table('equipos', schema=None) as batch_op:
    #     batch_op.add_column(sa.Column('imagen_lubricacion', sa.String(length=255), nullable=True))
    #     batch_op.alter_column('frecuencia_mantenimiento',
    #            existing_type=sa.VARCHAR(length=30),
    #            type_=sa.String(length=100),
    #            existing_nullable=True)
    pass
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('equipos', schema=None) as batch_op:
        batch_op.alter_column('frecuencia_mantenimiento',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=30),
               existing_nullable=True)
        batch_op.drop_column('imagen_lubricacion')

    # ### end Alembic commands ###
