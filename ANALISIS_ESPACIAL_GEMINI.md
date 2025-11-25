# 🗺️ Análisis Espacial y Visual con Gemini AI

## Resumen de Mejoras Implementadas

### ✨ Nuevas Capacidades

Este documento describe las mejoras implementadas para hacer el análisis de Gemini AI **espacialmente consciente** y **visualmente detallado**, proporcionando información mucho más útil y específica para los agricultores.

---

## 🎯 Objetivo

Mejorar el análisis de imágenes satelitales para que Gemini AI:
- **Analice visualmente** los cambios de color y vegetación entre meses
- **Use referencias espaciales** como "zona norte", "zona sur", etc.
- **Incorpore metadatos de EOSDA** (coordenadas, satélite, resolución, nubosidad)
- **Proporcione recomendaciones específicas por zona** dentro de la parcela

---

## 🛠️ Cambios Implementados

### 1. **Modelo de Datos Mejorado** (`models.py`)

Se agregaron nuevos campos al modelo `IndiceMensual`:

```python
# 🗺️ METADATOS ESPACIALES PARA ANÁLISIS VISUAL
metadatos_imagen = JSONField(
    # Metadatos completos de EOSDA: coordenadas, bbox, satélite, resolución, etc.
)
coordenadas_imagen = JSONField(
    # Bounding box y centroide: [min_lat, min_lon, max_lat, max_lon]
)
satelite_imagen = CharField(
    # Satélite que capturó la imagen (ej: Sentinel-2, Landsat-8)
)
resolucion_imagen = FloatField(
    # Resolución espacial en metros por píxel
)
```

**Beneficios:**
- Cada imagen satelital ahora tiene información espacial completa
- Se puede hacer análisis comparativo visual entre imágenes
- Gemini puede referenciar zonas específicas de la parcela

### 2. **Servicio de Gemini Mejorado** (`gemini_service.py`)

#### 2.1 Prompt Espacialmente Consciente

El prompt ahora incluye:
- Coordenadas del centroide y bounding box de la parcela
- Instrucciones explícitas para usar referencias espaciales
- Metadatos completos de cada imagen (fecha, satélite, resolución, nubosidad)
- Análisis comparativo visual mes a mes

**Ejemplo de prompt mejorado:**
```
**UBICACIÓN ESPACIAL DE LA PARCELA:**
- Centroide: Latitud 4.6234°N, Longitud -74.1567°W
- Bounding Box: 4.6200°N - 4.6268°N, -74.1600°W - -74.1534°W
- Para referencias espaciales, usa: 
  "zona norte" (cerca de 4.6268°N), 
  "zona sur" (cerca de 4.6200°N)
```

#### 2.2 Nuevos Métodos Auxiliares

**`_construir_descripcion_imagenes_espacial()`**
- Describe cada imagen con metadatos completos
- Incluye coordenadas, satélite, resolución
- Reporta calidad de datos (nubosidad)

**`_construir_analisis_comparativo_visual()`**
- Calcula cambios mes a mes en NDVI/NDMI
- Identifica incrementos/decrementos notables
- Sugiere interpretaciones visuales (ej: "probable aumento en vegetación visible")

**Ejemplo de salida:**
```
**Enero → Febrero:**
  - NDVI aumentó 0.087 (0.623 → 0.710) ⬆️ INCREMENTO NOTABLE
  → Visual: Probable aumento en vegetación/verdor visible en imágenes
```

### 3. **Generador de PDF Mejorado** (`generador_pdf.py`)

#### 3.1 Recopilación de Datos Espaciales

Ahora el generador:
- Extrae coordenadas del centroide y bounding box de la parcela
- Recopila metadatos espaciales de cada imagen
- Envía toda la información a Gemini para análisis contextualizado

```python
# Coordenadas de la parcela
if parcela.geometria:
    extent = parcela.geometria.extent
    parcela_data['coordenadas']['bbox'] = {
        'min_lon': extent[0],
        'min_lat': extent[1],
        'max_lon': extent[2],
        'max_lat': extent[3]
    }
```

#### 3.2 Nueva Sección en el PDF: "Análisis Visual de Imágenes"

El PDF ahora incluye una sección dedicada al análisis visual:

```python
### 🛰️ ANÁLISIS VISUAL DE IMÁGENES SATELITALES

[Descripción de cambios de color, patrones espaciales, 
 y variaciones visuales entre meses con referencias a 
 zonas específicas de la parcela]
```

**Características:**
- Caja destacada con fondo verde claro
- Solo se muestra si hay análisis visual disponible
- Incluye referencias espaciales y descripciones visuales

### 4. **Scripts de Utilidad**

#### 4.1 `actualizar_metadatos_espaciales.py`

Script para rellenar metadatos espaciales en imágenes existentes:

```bash
python actualizar_metadatos_espaciales.py
```

**Lo que hace:**
- Encuentra todos los índices con imágenes sin metadatos espaciales
- Genera coordenadas basadas en la geometría de la parcela
- Infiere el satélite (Sentinel-2/Landsat-8) basado en la fecha
- Asigna resolución espacial (10m para Sentinel-2)

#### 4.2 `test_analisis_espacial_gemini.py`

Script de prueba para validar el análisis espacial:

```bash
python test_analisis_espacial_gemini.py
```

**Validaciones:**
- Verifica que se incluyan coordenadas de la parcela
- Comprueba que se recopilen imágenes y metadatos
- Detecta referencias espaciales en el análisis
- Guarda el análisis en caché

---

## 📊 Ejemplo de Análisis Espacial

### Antes (Sin Referencias Espaciales):
```
El NDVI muestra una tendencia positiva. Se recomienda 
monitorear el riego en las áreas con bajo vigor.
```

### Después (Con Referencias Espaciales):
```
El NDVI muestra una tendencia positiva en toda la parcela, 
especialmente en la zona norte (cerca de 4.6268°N) donde 
el verdor aumentó notablemente en febrero.

La zona sur (4.6200°N) presenta heterogeneidad visible en 
las imágenes NDVI, con valores más bajos (0.45-0.55) que 
indican menor vigor vegetal. Se recomienda:

1. Inspeccionar zona sur para identificar causa del bajo NDVI
2. Ajustar riego focalizado en zona sur
3. Monitorear evolución de zona norte para mantener el vigor
```

---

## 🎨 Referencias Espaciales Utilizadas

El análisis de Gemini ahora puede usar:

| Referencia | Significado |
|-----------|-------------|
| **zona norte** | Área cercana a la latitud máxima (norte) |
| **zona sur** | Área cercana a la latitud mínima (sur) |
| **zona este** | Área cercana a la longitud máxima (menos negativa, este) |
| **zona oeste** | Área cercana a la longitud mínima (más negativa, oeste) |
| **centro de la parcela** | Área cercana al centroide |
| **heterogeneidad** | Variaciones espaciales dentro de la parcela |
| **uniformidad** | Distribución homogénea en toda la parcela |

---

## 📈 Beneficios para el Agricultor

### 1. **Información Accionable**
- Ya no solo dice "hay problemas", ahora dice **dónde están** los problemas
- Recomendaciones específicas por zona (ej: "inspeccionar zona sur")

### 2. **Mejor Comprensión Visual**
- Describe lo que se ve en las imágenes (cambios de color, verdor)
- Relaciona cambios visuales con índices numéricos

### 3. **Contexto Geográfico**
- Usa coordenadas reales de EOSDA
- Permite correlacionar con mapas y visitas de campo

### 4. **Trazabilidad de Calidad**
- Reporta metadatos de cada imagen (satélite, resolución, nubosidad)
- Advierte sobre datos de baja calidad

---

## 🚀 Uso

### 1. Actualizar Metadatos Espaciales (Primera Vez)

```bash
python actualizar_metadatos_espaciales.py
```

Esto rellena los campos nuevos en imágenes existentes.

### 2. Probar Análisis Espacial

```bash
python test_analisis_espacial_gemini.py
```

Genera un análisis de prueba y valida las referencias espaciales.

### 3. Generar Informe PDF

```bash
python manage.py shell
>>> from informes.generador_pdf import GeneradorPDFProfesional
>>> gen = GeneradorPDFProfesional()
>>> pdf_path = gen.generar_informe_completo(parcela_id=1, meses_atras=6)
>>> print(f"PDF generado: {pdf_path}")
```

El PDF ahora incluirá la sección de análisis visual con referencias espaciales.

### 4. Limpiar Caché (Si Necesitas Regenerar)

```bash
python manage.py shell
>>> from informes.models import IndiceMensual
>>> IndiceMensual.objects.update(analisis_gemini=None, fecha_analisis_gemini=None)
>>> print("Caché limpiado")
```

---

## 🔧 Migración de Datos

La migración `0012_agregar_metadatos_espaciales` agrega los nuevos campos:

```bash
python manage.py migrate
```

Los campos son **opcionales** (null=True), por lo que no rompe datos existentes.

---

## 📝 Estructura del Análisis Gemini

El análisis ahora tiene estas secciones:

```json
{
  "resumen_ejecutivo": "...",
  "analisis_tendencias": "...",
  "analisis_visual": "... (NUEVO: análisis visual espacialmente consciente)",
  "recomendaciones": "...",
  "alertas": "...",
  "texto_completo": "..."
}
```

---

## 💰 Impacto en Costos

- **Sin cambios significativos**: El análisis usa el mismo modelo (Gemini 2.5 Flash)
- **Tokens adicionales**: ~200-400 tokens más por análisis (metadatos espaciales)
- **Costo incremental**: ~$0.0001-0.0002 USD por análisis
- **Valor añadido**: Análisis mucho más útil y accionable

---

## ✅ Validaciones Automáticas

El script de prueba valida:

- ✅ Resumen ejecutivo presente
- ✅ Análisis de tendencias presente
- ✅ **Análisis visual presente** (nuevo)
- ✅ Recomendaciones presentes
- ✅ Incluye imágenes en análisis
- ✅ Incluye datos espaciales
- ✅ **Referencias espaciales detectadas** (nuevo)

---

## 🐛 Solución de Problemas

### Problema: "No se detectaron referencias espaciales"

**Causa:** La parcela no tiene geometría o centroide definido.

**Solución:**
```python
parcela = Parcela.objects.get(id=1)
if not parcela.geometria:
    # Asignar geometría desde coordenadas JSON
    from django.contrib.gis.geos import GEOSGeometry
    parcela.geometria = GEOSGeometry(parcela.coordenadas)
    parcela.save()
```

### Problema: "Análisis visual no disponible"

**Causa:** No hay imágenes satelitales descargadas.

**Solución:**
```bash
# Descargar imágenes desde EOSDA
python actualizar_datos_clima_todas_parcelas.py
```

---

## 📚 Documentos Relacionados

- `INTEGRACION_GEMINI_COMPLETA.md` - Documentación de la integración inicial
- `RESUMEN_EJECUTIVO_GEMINI.md` - Resumen ejecutivo del sistema
- `FLUJO_IMAGENES_SATELITALES.md` - Flujo de descarga de imágenes

---

## 🎉 Conclusión

Las mejoras implementadas transforman el análisis de Gemini de un reporte genérico a un **análisis espacialmente consciente y visualmente detallado**, proporcionando información mucho más útil y accionable para los agricultores.

**Características clave:**
- 🗺️ Referencias espaciales (zona norte, sur, etc.)
- 📸 Análisis visual de cambios entre imágenes
- 🛰️ Metadatos completos de EOSDA
- 🎯 Recomendaciones específicas por zona
- 💾 Sistema de caché para optimización de costos

---

**Fecha de implementación:** 21 de noviembre de 2025  
**Versión:** 2.0 - Análisis Espacial
