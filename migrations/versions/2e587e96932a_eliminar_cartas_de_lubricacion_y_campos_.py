"""Eliminar cartas de lubricacion y campos relacionados

Revision ID: 2e587e96932a
Revises: 989edf4ee0dd
Create Date: [fecha_actual]

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e587e96932a'
down_revision = '989edf4ee0dd'
branch_labels = None
depends_on = None


def upgrade():
    # Eliminar la tabla de lubricación si existe
    try:
        op.drop_table('lubricacion')
    except:
        pass  # La tabla no existe
    
    # Eliminar los campos de la tabla equipos
    with op.batch_alter_table('equipos') as batch_op:
        try:
            batch_op.drop_column('imagen_lubricacion')
        except:
            pass  # La columna no existe
        try:
            batch_op.drop_column('cartas_lubricacion')
        except:
            pass  # La columna no existe


def downgrade():
    # Volver a crear los campos y la tabla si se revierte la migración
    with op.batch_alter_table('equipos') as batch_op:
        batch_op.add_column(sa.Column('imagen_lubricacion', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('cartas_lubricacion', sa.String(length=20), nullable=True))
    
    op.create_table(
        'lubricacion',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('equipo_codigo', sa.String(50), sa.ForeignKey('equipos.codigo'), nullable=False),
        sa.Column('numero', sa.Integer),
        sa.Column('mecanismo', sa.String(200)),
        sa.Column('cantidad', sa.String(50)),
        sa.Column('tipo_lubricante', sa.String(100)),
        sa.Column('producto', sa.String(100)),
        sa.Column('metodo_lubricacion', sa.String(100)),
        sa.Column('frecuencia_inspeccion', sa.String(100)),
        sa.Column('observaciones', sa.Text)
    )
