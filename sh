source venv/bin/activate
#!/bin/bash
# Script de actualización automatizada para mantenimiento_app en producción
# Ejecutar con: bash actualizar_produccion.sh

set -e

# 1. Backup de base de datos y archivos importantes
echo "==============================="
echo "��️ 1. Backup de base de datos y archivos"
echo "==============================="
fecha=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
cp instance/mantenimiento.db backups/mantenimiento_backup_$fecha.db
cp -r static/uploads backups/uploads_backup_$fecha

echo "✅ Backup realizado en backups/"

# 2. (Opcional) Activar entorno virtual
echo "==============================="
echo "🐍 2. Activando entorno virtual"
echo "==============================="
if [ -d ".venv" ]; then
    source . venv/bin/activate
    echo "✅ Entorno virtual activado"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️ No se encontró entorno virtual. Abortando."
    exit 1
fi

echo "✅ Entorno virtual activado"

# 3. Actualizar dependencias
echo "==============================="
echo "📦 3. Actualizando dependencias"
echo "==============================="
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencias actualizadas"

# 4. Aplicar migraciones
echo "==============================="
echo "🗄️ 4. Aplicando migraciones"
echo "==============================="
if [ -f "verificar_migraciones_produccion.py" ]; then
    python verificar_migraciones_produccion.py < <(echo "s")
else
    flask db upgrade || alembic upgrade head
fi

echo "✅ Migraciones aplicadas"

# 5. Reiniciar servicios
echo "==============================="
echo "🔄 5. Reiniciando servicios"
echo "==============================="
sudo systemctl restart mantenimiento_app
sudo systemctl restart nginx

echo "✅ Servicios reiniciados"

# 6. Limpiar caché de archivos estáticos (opcional)
echo "==============================="
echo "�� 6. Limpiar caché (manual en navegador)"
echo "==============================="
echo "💡 Recuerda hacer Ctrl+F5 en el navegador y verificar la app"

echo "🎉 Actualización completada. Verifica la aplicación en producción."
