#!/bin/bash
# Script de inicialización para Railway
# Habilita PostGIS y ejecuta migraciones

set -e  # Exit on error

echo "🚀 Iniciando aplicación AgroTech en Railway..."

# Configurar Django settings
export DJANGO_SETTINGS_MODULE=agrotech_historico.settings_production

# Verificar que DATABASE_URL existe
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no está configurada"
    exit 1
fi

echo "✅ DATABASE_URL configurada"

# Habilitar extensiones PostGIS en PostgreSQL
echo "🗄️  Habilitando extensiones PostGIS en PostgreSQL..."
python << END
import os
import psycopg2
from urllib.parse import urlparse

# Parsear DATABASE_URL
db_url = urlparse(os.getenv('DATABASE_URL'))

try:
    # Conectar a PostgreSQL
    conn = psycopg2.connect(
        database=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port
    )
    conn.set_isolation_level(0)  # AUTOCOMMIT
    cursor = conn.cursor()
    
    # Habilitar extensiones
    print("Habilitando PostGIS...")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    print("✅ PostGIS habilitado")
    
    print("Habilitando PostGIS Topology...")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
    print("✅ PostGIS Topology habilitado")
    
    cursor.close()
    conn.close()
    print("✅ Extensiones PostGIS configuradas correctamente")
except Exception as e:
    print(f"⚠️  Warning: No se pudieron habilitar extensiones PostGIS: {e}")
    print("   (Esto es normal si ya están habilitadas)")
END

# Ejecutar migraciones de Django
echo "📦 Ejecutando migraciones de Django..."
python manage.py migrate --noinput

echo "✅ Migraciones completadas"

# Recopilar archivos estáticos (por si falló en build)
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput || echo "⚠️  Collectstatic falló, continuando..."

echo "🎯 Iniciando servidor Gunicorn..."
# Iniciar Gunicorn
exec gunicorn agrotech_historico.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
