# Dockerfile para AgroTech - Optimizado para Railway con GeoDjango
FROM python:3.10-slim

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

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
    libproj-dev \
    # Limpieza
    && rm -rf /var/lib/apt/lists/*

# Variables de entorno para GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (para cachear instalación de dependencias)
COPY requirements.txt .

# Actualizar pip e instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles

# Recopilar archivos estáticos (se ejecutará en build)
RUN python manage.py collectstatic --noinput || echo "Collectstatic fallido, continuando..."

# Exponer puerto (Railway usa variable $PORT)
EXPOSE ${PORT:-8000}

# Script de inicio
CMD ["sh", "-c", "python manage.py migrate && gunicorn agrotech_historico.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
