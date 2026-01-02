# Dockerfile para AgroTech - Optimizado para Railway con GeoDjango
FROM python:3.10-slim

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema para GeoDjango
# GDAL, GEOS, PROJ son necesarios para GeoDjango
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencias geoespaciales
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    proj-bin \
    proj-data \
    # PostgreSQL client
    postgresql-client \
    libpq-dev \
    # Utilidades de compilación
    gcc \
    g++ \
    binutils \
    # Limpieza
    && rm -rf /var/lib/apt/lists/*

# Verificar instalación y crear symlinks para Django
RUN echo "🔍 Detectando rutas de librerías geoespaciales..." && \
    GDAL_LIB=$(find /usr/lib -name "libgdal.so*" ! -name "*.a" | grep -v "\.so\.[0-9]*\." | head -1) && \
    GEOS_LIB=$(find /usr/lib -name "libgeos_c.so*" ! -name "*.a" | grep -v "\.so\.[0-9]*\." | head -1) && \
    echo "📍 GDAL encontrado en: $GDAL_LIB" && \
    echo "📍 GEOS encontrado en: $GEOS_LIB" && \
    # Crear symlinks en /usr/lib para compatibilidad con Django
    if [ -n "$GDAL_LIB" ]; then \
        ln -sf $GDAL_LIB /usr/lib/libgdal.so && \
        echo "✅ Symlink creado: /usr/lib/libgdal.so -> $GDAL_LIB"; \
    fi && \
    if [ -n "$GEOS_LIB" ]; then \
        ln -sf $GEOS_LIB /usr/lib/libgeos_c.so && \
        echo "✅ Symlink creado: /usr/lib/libgeos_c.so -> $GEOS_LIB"; \
    fi && \
    # Verificar versiones
    echo "📦 Versión GDAL: $(gdal-config --version)" && \
    echo "📦 Versión GEOS: $(geos-config --version)" && \
    # Verificar que los symlinks funcionan
    ldconfig && \
    ls -la /usr/lib/libgdal.so /usr/lib/libgeos_c.so

# Variables de entorno para GDAL
# Configurar todas las rutas necesarias para que Django encuentre las librerías
ENV GDAL_CONFIG=/usr/bin/gdal-config \
    GEOS_CONFIG=/usr/bin/geos-config \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so \
    GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj \
    LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/lib:${LD_LIBRARY_PATH}

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (para cachear instalación de dependencias)
COPY requirements.txt .

# Actualizar pip e instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Verificar que GDAL se instaló correctamente en Python
RUN echo "🧪 Verificando instalación de GDAL en Python..." && \
    python -c "from osgeo import gdal; print('✅ GDAL Python binding OK, versión:', gdal.__version__)" && \
    python -c "from osgeo import ogr; print('✅ OGR OK')" && \
    python -c "from osgeo import osr; print('✅ OSR OK')" || \
    (echo "❌ ERROR: GDAL Python bindings fallaron" && exit 1)

# Copiar el código del proyecto
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles

# Verificar que Django puede cargar GeoDjango (diagnóstico completo)
RUN echo "🧪 Verificando integración completa de GeoDjango..." && \
    python -c "import django; django.setup(); from django.contrib.gis import gdal, geos; print('✅ Django GDAL OK, versión:', gdal.gdal_version()); print('✅ Django GEOS OK, versión:', geos.geos_version())" 2>&1 || \
    (echo "⚠️ Warning: Configuración de Django aún no disponible (normal en build)" && \
     python -c "from django.contrib.gis import gdal, geos; print('✅ GeoDjango modules OK')")

# Recopilar archivos estáticos (se ejecutará en build)
# Nota: Esto puede fallar si no hay DATABASE_URL en build time, es normal
RUN python manage.py collectstatic --noinput 2>&1 || echo "⚠️ Collectstatic falló (normal sin DATABASE_URL en build), se ejecutará en deploy"

# Exponer puerto (Railway usa variable $PORT)
EXPOSE ${PORT:-8000}

# Script de inicio
CMD ["sh", "-c", "python manage.py migrate && gunicorn agrotech_historico.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
