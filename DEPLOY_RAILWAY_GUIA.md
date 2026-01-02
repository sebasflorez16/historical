# 🚂 GUÍA DE DESPLIEGUE EN RAILWAY - AGROTECH

## ✅ ARCHIVOS CREADOS (YA LISTOS)

Los siguientes archivos han sido creados y configurados en tu proyecto:

1. ✅ **Dockerfile** - Configuración de Docker con GeoDjango
2. ✅ **.dockerignore** - Archivos a excluir del build
3. ✅ **railway.toml** - Configuración de Railway
4. ✅ **requirements.txt** - Dependencias actualizadas (con GDAL 3.6.2)
5. ✅ **settings_production.py** - Settings optimizados para producción

---

## 📋 PASO 1: VERIFICAR ARCHIVOS LOCALMENTE

Ejecuta estos comandos para verificar que todo está listo:

```bash
# 1. Verificar que los archivos existen
ls -la Dockerfile railway.toml .dockerignore

# 2. Ver contenido del Dockerfile
cat Dockerfile

# 3. Ver requirements.txt
cat requirements.txt
```

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 2: PREPARAR SETTINGS.PY PARA PRODUCCIÓN

Necesitamos actualizar tu `agrotech_historico/settings.py` para que funcione tanto en desarrollo como en producción.

### Opción A: Usar settings_production.py (RECOMENDADO)

Renombra o respalda tu `settings.py` actual y usa `settings_production.py`:

```bash
# Respaldar settings actual
mv agrotech_historico/settings.py agrotech_historico/settings_backup.py

# Copiar settings de producción
cp settings_production.py agrotech_historico/settings.py
```

### Opción B: Modificar tu settings.py existente

Si prefieres mantener tu configuración actual, asegúrate de incluir:

```python
# Al inicio del archivo
import os
import dj_database_url

# DATABASE
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            engine='django.contrib.gis.db.backends.postgis'
        )
    }

# STATIC FILES
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MIDDLEWARE (agregar whitenoise)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # AÑADIR AQUÍ
    # ... resto de middleware
]
```

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 3: COMMIT Y PUSH A GITHUB

Ahora vamos a subir todos los cambios a GitHub:

```bash
# 1. Ver archivos modificados
git status

# 2. Agregar todos los archivos nuevos
git add Dockerfile .dockerignore railway.toml requirements.txt settings_production.py

# 3. Commit
git commit -m "Configurar proyecto para Railway con Docker y GeoDjango"

# 4. Push a GitHub
git push origin main
```

**⚠️ IMPORTANTE:** Si no tienes repositorio en GitHub, créalo primero:

```bash
# Crear repo en GitHub (ve a github.com y crea un repo llamado "agrotech-historico")

# Luego conecta tu repo local:
git remote add origin https://github.com/TU_USUARIO/agrotech-historico.git
git branch -M main
git push -u origin main
```

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 4: CREAR PROYECTO EN RAILWAY

1. Ve a [railway.app](https://railway.app)
2. Inicia sesión con tu cuenta de GitHub
3. Clic en **"New Project"**
4. Selecciona **"Deploy from GitHub repo"**
5. Busca y selecciona tu repositorio **"agrotech-historico"**
6. Railway detectará automáticamente el `Dockerfile`

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 5: AGREGAR BASE DE DATOS POSTGRESQL

En tu proyecto de Railway:

1. Clic en **"+ New"** (botón en la esquina superior derecha)
2. Selecciona **"Database"**
3. Selecciona **"PostgreSQL"**
4. Railway creará automáticamente la base de datos y generará `DATABASE_URL`

### Habilitar PostGIS:

1. En el servicio PostgreSQL, clic en **"Data"** o **"Connect"**
2. Copia el **"Connection URL"** (o usa el cliente de Railway)
3. Ejecuta en la consola de Railway (pestaña "Query" o "Console"):

```sql
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 6: CONFIGURAR VARIABLES DE ENTORNO

En tu proyecto de Railway, ve a la pestaña **"Variables"** del servicio web y agrega:

```env
# Django
SECRET_KEY=genera-una-clave-secreta-fuerte-aqui-usa-python-secrets
DEBUG=False
ALLOWED_HOSTS=*.up.railway.app,*.railway.app
DJANGO_SETTINGS_MODULE=agrotech_historico.settings

# APIs externas
GEMINI_API_KEY=tu_clave_gemini_aqui
EOSDA_API_KEY=tu_clave_eosda_aqui

# Email (Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_password_aplicacion_gmail
DEFAULT_FROM_EMAIL=tu_email@gmail.com

# Base de datos (Railway lo configura automáticamente)
# DATABASE_URL ya está configurada por Railway
```

### Generar SECRET_KEY:

```python
# En tu terminal local, ejecuta:
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copia el resultado y úsalo como `SECRET_KEY`.

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 7: AGREGAR VOLUMEN PERSISTENTE PARA MEDIA FILES

En tu servicio web de Railway:

1. Ve a **"Settings"** → **"Volumes"**
2. Clic en **"+ Add Volume"**
3. Configura:
   - **Mount Path:** `/app/media`
   - **Size:** 5 GB (gratis hasta 5GB)
4. Guarda

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 8: VERIFICAR DEPLOY Y LOGS

Railway desplegará automáticamente tu proyecto:

1. Ve a la pestaña **"Deployments"**
2. Observa el progreso del build
3. Verifica los logs en tiempo real

### Validar que GDAL se instaló correctamente:

En los logs deberías ver:

```
✅ Installing gdal-bin
✅ Installing libgdal-dev
✅ Installing libgeos-dev
✅ Installing libproj-dev
```

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 9: EJECUTAR MIGRACIONES

Una vez que el deploy sea exitoso:

1. En Railway, ve a tu servicio web
2. Abre la **"Console"** (terminal)
3. Ejecuta:

```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Verificar que GDAL funciona
python manage.py shell
>>> from django.contrib.gis.gdal import GDAL_VERSION
>>> print(GDAL_VERSION)
>>> exit()
```

**✋ CONFIRMA ESTE PASO ANTES DE CONTINUAR**

---

## 📋 PASO 10: PROBAR LA APLICACIÓN

1. En Railway, copia la URL pública de tu servicio (aparece en la parte superior)
2. Abre en tu navegador: `https://tu-app.up.railway.app`
3. Prueba el admin: `https://tu-app.up.railway.app/admin/`
4. Verifica que puedes crear parcelas con geometrías

---

## 🎉 ¡LISTO!

Tu aplicación AgroTech está desplegada en Railway con:

✅ Django + GeoDjango  
✅ PostgreSQL + PostGIS  
✅ GDAL, GEOS, PROJ (librerías geoespaciales)  
✅ Almacenamiento persistente para imágenes  
✅ Variables de entorno seguras  
✅ SSL automático (HTTPS)  
✅ Deploy automático desde GitHub  

---

## 🔧 TROUBLESHOOTING

### Error: "GDAL version mismatch"

En la consola de Railway:
```bash
gdal-config --version
# Actualiza requirements.txt con esa versión exacta
# Ejemplo: GDAL==3.6.4
```

### Error: "PostGIS extension not found"

En PostgreSQL de Railway:
```sql
CREATE EXTENSION postgis;
```

### Error: "Static files not found"

```bash
python manage.py collectstatic --noinput
```

---

## 💰 COSTOS ESTIMADOS

- **Web Service:** ~$5/mes (incluido en crédito gratis)
- **PostgreSQL:** ~$5/mes (incluido en crédito gratis)
- **Almacenamiento:** Gratis hasta 5GB
- **Total:** $0/mes (con crédito gratis de $5)

Después del crédito gratis: ~$10-15/mes para uso ligero.

---

**¿TODO LISTO? AHORA COMIENZA CON EL PASO 1** ✅
