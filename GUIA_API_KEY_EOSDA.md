# 🔑 GUÍA RÁPIDA: Configurar API Key de EOSDA

## ⏱️ Tiempo estimado: 5 minutos

---

## 📋 Pasos para Obtener API Key

### 1️⃣ Acceder al Dashboard de EOSDA

1. Abrir en el navegador: **https://eos.com/dashboard**
2. Hacer clic en **"Sign In"** o **"Log In"**
3. Ingresar tus credenciales de EOSDA

> **¿No tienes cuenta?**  
> Crear una cuenta en: https://eos.com/pricing  
> (Tienen plan gratuito con límites razonables)

---

### 2️⃣ Navegar a API Keys

Una vez dentro del dashboard:

1. Buscar el menú lateral o superior
2. Hacer clic en **"Settings"** o **"Account Settings"**
3. Seleccionar **"API Keys"** o **"Developers"**

---

### 3️⃣ Generar Nueva API Key

1. Hacer clic en **"Generate New API Key"** o **"Create API Key"**
2. **IMPORTANTE:** Copiar la key completa inmediatamente
   - La key solo se muestra UNA VEZ
   - Debe empezar con `apk.`
   - Debe tener aproximadamente 68 caracteres
3. Guardar la key en un lugar seguro (ej: administrador de contraseñas)

**Ejemplo de API key válida:**
```
apk.1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

---

### 4️⃣ Verificar Permisos

Asegurarse de que la cuenta tenga acceso a:

- ✅ **Field Management API** (para crear/gestionar parcelas)
- ✅ **Statistics API** (para obtener datos satelitales)
- ✅ **Sin restricciones de dominio**

Si hay opciones de permisos al crear la key, seleccionar:
- [x] Field Management
- [x] Statistics
- [x] All domains / No restrictions

---

## 🚀 Configurar en Railway

### Opción A: Desde la Web de Railway (Recomendado)

1. Ir a **https://railway.app**
2. Hacer clic en tu proyecto **"AgroTech Histórico"**
3. Hacer clic en la pestaña **"Variables"**
4. Buscar la variable **`EOSDA_API_KEY`**
5. Hacer clic en **"Edit"** o el ícono de lápiz
6. Pegar la nueva API key completa
7. Hacer clic en **"Save"** o **"Update"**

✅ Railway se redespleigará automáticamente (2-3 minutos)

---

### Opción B: Desde Railway CLI

Si tienes Railway CLI instalado:

```bash
# Instalar Railway CLI (si no lo tienes)
npm install -g @railway/cli

# Login
railway login

# Listar proyectos
railway list

# Seleccionar proyecto
railway link

# Actualizar variable
railway variables set EOSDA_API_KEY=apk.tu_api_key_aqui
```

---

## ✅ Verificar que Funciona

### Opción 1: Desde la Aplicación Web

1. Esperar 2-3 minutos después de actualizar la variable
2. Ir a tu aplicación: **https://agrotech-historico-production.up.railway.app**
3. Iniciar sesión en el admin
4. Crear o editar una parcela
5. Intentar sincronizar con EOSDA
6. Debería mostrar **"Estado: Conectado"** ✅

---

### Opción 2: Ejecutar Script de Diagnóstico

Desde tu terminal local:

```bash
# Asegurarse de tener la nueva key en el .env local
echo "EOSDA_API_KEY=apk.tu_nueva_key" >> .env

# Ejecutar diagnóstico
python diagnostico_eosda_simple.py
```

Debería mostrar:
```
✅ ÉXITO - La API key funciona correctamente
```

---

### Opción 3: Desde Railway (verificación en producción)

```bash
# Conectar a Railway
railway link

# Ejecutar script de verificación
railway run python verificar_sistema.py
```

Debería mostrar:
```
✅ EOSDA: Conectado (X campos)
```

---

## ❓ Solución de Problemas

### Error: "Missing Authentication Token"

**Causa:** API key inválida, expirada o mal copiada

**Solución:**
1. Verificar que copiaste la key completa (debe tener ~68 caracteres)
2. Verificar que empiece con `apk.`
3. Verificar que no tenga espacios al inicio o final
4. Generar una nueva key en el dashboard de EOSDA

---

### Error: "Invalid API Key"

**Causa:** La key fue revocada o la cuenta no tiene permisos

**Solución:**
1. Ir al dashboard de EOSDA
2. Verificar que la key esté activa (no dice "Revoked")
3. Verificar que la cuenta tenga plan activo
4. Generar una nueva key si es necesario

---

### Error: "Access Denied" o "Forbidden"

**Causa:** Restricciones de dominio o IP

**Solución:**
1. En el dashboard de EOSDA, ir a API Key settings
2. Verificar que no haya restricciones de dominio
3. Si hay restricciones, agregar: `*.railway.app`
4. O deshabilitar restricciones completamente

---

### La app sigue usando datos simulados

**Causa:** La variable en Railway no se actualizó correctamente

**Solución:**
1. Verificar que la variable `EOSDA_API_KEY` en Railway esté actualizada
2. Hacer un redeploy manual:
   ```bash
   railway up --detach
   ```
3. Verificar los logs:
   ```bash
   railway logs
   ```
4. Buscar mensajes tipo "EOSDA configurado correctamente"

---

## 📊 Verificar Estado Actual

### Variables de Entorno en Railway

Debe tener configuradas:

```bash
EOSDA_API_KEY=apk.tu_api_key_real_aqui
EOSDA_BASE_URL=https://api.eos.com
```

### Logs de Railway

Buscar en los logs mensajes como:

✅ Correcto:
```
✓ EOSDA configurado correctamente
✓ Campo creado exitosamente en EOSDA con ID: 12345
```

❌ Error:
```
❌ Error creando campo en EOSDA: Missing Authentication Token
⚠️  Token de EOSDA no configurado correctamente
```

---

## 💡 Consejos Importantes

### ✅ Hacer

- ✅ Copiar la API key completa cuando se genera
- ✅ Guardarla en un administrador de contraseñas
- ✅ Verificar que funciona antes de cerrar el dashboard
- ✅ Actualizar la variable en Railway inmediatamente

### ❌ NO Hacer

- ❌ Compartir la API key públicamente
- ❌ Subirla a Git (ya está en .gitignore)
- ❌ Usar la key de demo en producción
- ❌ Olvidar copiarla (solo se muestra una vez)

---

## 📞 Contacto de Soporte

### Si nada funciona:

**Soporte de EOSDA:**
- Email: **support@eos.com**
- Web: https://eos.com/contact

**Información a proporcionar:**
- Prefijo de tu API key (primeros 15 caracteres)
- Error exacto que recibes
- Que necesitas acceso a Field Management API

---

## 🎯 Checklist Final

- [ ] Obtuve la API key de EOSDA
- [ ] La key empieza con `apk.`
- [ ] La key tiene ~68 caracteres
- [ ] Actualicé la variable en Railway
- [ ] Esperé 2-3 minutos para el redeploy
- [ ] Verifiqué que funciona (script o app web)
- [ ] La sincronización con EOSDA funciona ✅

---

## 🔗 Enlaces Útiles

- **Dashboard EOSDA:** https://eos.com/dashboard
- **Documentación API:** https://doc.eos.com/
- **Pricing (planes):** https://eos.com/pricing
- **Railway Dashboard:** https://railway.app
- **Tu App:** https://agrotech-historico-production.up.railway.app

---

*Última actualización: 2026-01-02*  
*Si tienes problemas, ejecuta: `python diagnostico_eosda_simple.py`*
