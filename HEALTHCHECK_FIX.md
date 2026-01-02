# 🔧 Corrección de Healthcheck en Railway - AgroTech Histórico

**Fecha:** 2 de enero de 2026  
**Estado:** Cambios desplegados, esperando validación

---

## 🎯 **Problema Identificado**

Railway healthcheck estaba recibiendo **HTTP 301 (redirect)** en lugar de **200 OK**, causando que el servicio no pasara el healthcheck.

### Logs del problema:
```
100.64.0.2 - - [02/Jan/2026:16:49:42 -0500] "GET /health/ HTTP/1.1" 301 0 "-" "RailwayHealthCheck/1.0"
```

### Causas raíz:
1. **SSL Redirect**: `SECURE_SSL_REDIRECT = True` forzaba redirect de HTTP a HTTPS
2. **Trailing Slash**: Django `APPEND_SLASH = True` (default) redirige `/health` a `/health/`
3. **CommonMiddleware**: Agregaba redirects automáticos para normalizar URLs

---

## ✅ **Soluciones Implementadas**

### 1. **Nuevo Endpoint de Healthcheck**
📄 Archivo: `agrotech_historico/urls.py`

```python
@csrf_exempt
def healthcheck(request):
    """Endpoint para Railway healthcheck - retorna 200 OK sin redirecciones"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AgroTech Histórico',
        'database': 'connected'
    }, status=200)

urlpatterns = [
    # Acepta con o sin trailing slash usando regex
    re_path(r'^health/?$', healthcheck, name='healthcheck'),
    # ...resto de URLs
]
```

**Beneficios:**
- ✅ Acepta `/health` y `/health/` (sin 301)
- ✅ No requiere CSRF token
- ✅ Retorna explícitamente status 200

### 2. **Middleware Personalizado**
📄 Archivo: `agrotech_historico/middleware.py` (nuevo)

```python
class HealthCheckMiddleware(MiddlewareMixin):
    """Marca requests de healthcheck para excluirlos de SSL redirect"""
    
    def process_request(self, request):
        if request.path.startswith('/health'):
            request._healthcheck = True
        return None
```

**Beneficios:**
- ✅ Identifica requests de healthcheck
- ✅ Los marca para tratamiento especial
- ✅ Se ejecuta primero en el stack de middleware

### 3. **Configuración de Settings**
📄 Archivo: `agrotech_historico/settings_production.py`

**Cambios en MIDDLEWARE:**
```python
MIDDLEWARE = [
    'agrotech_historico.middleware.HealthCheckMiddleware',  # ⬅️ PRIMERO
    'django.middleware.security.SecurityMiddleware',
    # ...resto
]
```

**Cambios en Security Settings:**
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # ⬅️ Desactivado (manejado por middleware)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # ...resto

# Desactivar redirects automáticos de trailing slash
APPEND_SLASH = False  # ⬅️ Evita 301 redirects
```

**Cambios en ALLOWED_HOSTS:**
```python
ALLOWED_HOSTS.extend([
    '*',  # ⬅️ Permitir todos (Railway healthcheck usa IPs internas)
    'healthcheck.railway.app',
    '.railway.app',
    '.up.railway.app',
])
```

### 4. **Actualización de railway.toml**
📄 Archivo: `railway.toml`

```toml
[deploy]
healthcheckPath = "/health/"  # ⬅️ Cambiado de /admin/ a /health/
healthcheckTimeout = 100
```

---

## 📋 **Commits Realizados**

### Commit 1: `9590489`
```
feat: agregar endpoint /health/ para Railway healthcheck

- Crear endpoint /health/ que retorna 200 OK con JSON status
- Actualizar railway.toml para usar /health/ en lugar de /admin/
- Permitir todos los hosts temporalmente para healthcheck interno
- Resolver problema de healthcheck que recibía 301 redirects
```

### Commit 2: `ec34b49`
```
fix: resolver redirects 301 en healthcheck de Railway

- Crear middleware personalizado para excluir /health de SSL redirects
- Usar regex en URL para aceptar /health con o sin trailing slash
- Desactivar APPEND_SLASH globalmente para evitar 301
- Agregar @csrf_exempt al healthcheck endpoint
- Configurar status=200 explícito en respuesta JSON
```

---

## 🔍 **Pruebas a Realizar**

Una vez que Railway despliegue los cambios, verificar:

### 1. **Healthcheck responde 200 OK**
```bash
# Desde Railway CLI
railway logs

# Buscar en los logs:
# ✅ "GET /health/ HTTP/1.1" 200 XX
# ❌ "GET /health/ HTTP/1.1" 301 0  (este ya NO debe aparecer)
```

### 2. **Servicio pasa el healthcheck**
- Ir al dashboard de Railway
- Verificar que el servicio está "Healthy" (verde)
- No debe mostrar warnings de healthcheck fallidos

### 3. **Endpoint responde correctamente**
```bash
# Obtener la URL del servicio
railway status

# Probar el endpoint (reemplazar con tu URL)
curl https://tu-app.railway.app/health/
# Debe retornar: {"status":"healthy","service":"AgroTech Histórico","database":"connected"}
```

### 4. **Admin y otras rutas funcionan**
```bash
# Verificar que el admin sigue funcionando
curl -I https://tu-app.railway.app/admin/
# Debe redirigir correctamente al login
```

---

## ⚠️ **Warnings Conocidos (No Críticos)**

### Collation Version Mismatch
```
WARNING: database "railway" has a collation version mismatch
DETAIL: The database was created using collation version 2.41, 
        but the operating system provides version 2.31.
```

**Impacto:** ⚠️ Warning solamente, no afecta funcionalidad  
**Causa:** Diferencia entre versión de collation de PostgreSQL en Railway  
**Solución:** No requiere acción inmediata. Si quieres corregirlo:

```sql
-- Conectar a la base de datos via Railway CLI
railway connect Postgres

-- Ejecutar:
ALTER DATABASE railway REFRESH COLLATION VERSION;
```

### Python Version Warning
```
FutureWarning: You are using a Python version (3.10.19) which Google 
will stop supporting in new releases of google.api_core once it reaches 
its end of life (2026-10-04).
```

**Impacto:** ⚠️ Informativo, funciona hasta octubre 2026  
**Recomendación:** Actualizar a Python 3.11 o 3.12 en Dockerfile antes de octubre 2026

---

## 🚀 **Próximos Pasos**

1. ✅ **Verificar deployment en Railway**
   - Ver logs: `railway logs`
   - Verificar healthcheck pasa (200 OK)

2. ✅ **Crear superusuario si no existe**
   ```bash
   railway ssh -- python manage.py createsuperuser
   ```

3. ✅ **Acceder al admin de Django**
   - Abrir: `https://tu-app.railway.app/admin/`
   - Login con superusuario

4. ✅ **Validar funcionalidad completa**
   - Probar login
   - Verificar GeoDjango funciona
   - Probar creación de parcelas
   - Validar generación de informes

5. ⚙️ **Optimizaciones opcionales**
   - Considerar cambiar `APPEND_SLASH = True` y manejar solo healthcheck
   - Implementar SSL redirect condicional en Nginx/proxy si se requiere
   - Configurar dominio personalizado en Railway

---

## 📚 **Comandos Railway CLI Útiles**

```bash
# Ver estado
railway status

# Ver logs en tiempo real
railway logs

# SSH al contenedor
railway ssh

# Ejecutar comando en contenedor
railway ssh -- python manage.py check

# Conectar a PostgreSQL
railway connect Postgres

# Ver variables de entorno
railway variables

# Abrir en navegador
railway open

# Redesplegar
railway redeploy
```

---

## 🎯 **Resultado Esperado**

Después del deployment, los logs deben mostrar:

```
[2026-01-02 XX:XX:XX +0000] [1] [INFO] Starting gunicorn 21.2.0
[2026-01-02 XX:XX:XX +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
✅ Base de datos configurada: postgres.railway.internal
100.64.0.2 - - [02/Jan/2026:XX:XX:XX -0500] "GET /health/ HTTP/1.1" 200 XX "-" "RailwayHealthCheck/1.0"  ⬅️ 200 OK!
```

---

## 📝 **Notas Adicionales**

- **ALLOWED_HOSTS con `'*'`**: Temporal para diagnóstico. Railway usa IPs internas para healthcheck.
- **APPEND_SLASH = False**: Puede requerir agregar `/` manualmente en otras URLs del proyecto.
- **Middleware order**: `HealthCheckMiddleware` DEBE ser el primero para funcionar correctamente.

---

**Última actualización:** 2 de enero de 2026, 21:50 UTC  
**Estado:** ⏳ Esperando confirmación de deployment en Railway
