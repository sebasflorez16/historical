# 🎬 Timeline Visual - Guía Rápida de Uso

## 📍 Ubicación del Timeline

### 1. Desde el Detalle de Parcela

```
Parcelas → [Seleccionar Parcela] → Detalle Parcela
```

En la página de detalle verás:

```
┌─────────────────────────────────────────────────┐
│  📊 Datos Disponibles                           │
│  12 meses (Ene 2024 - Dic 2024)                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  [🛰️ Datos EOSDA]                               │
│  [✓ Sincronizada]                               │
│  [💾 Datos Guardados]                           │
│  [📄 Generar Informe]                           │
│  [🎬 Timeline Visual]  ← NUEVO BOTÓN            │
└─────────────────────────────────────────────────┘
```

---

## 🎮 Interfaz del Timeline

### Pantalla Principal

```
╔══════════════════════════════════════════════════════════════╗
║              🎬 Timeline Visual                              ║
║          Parcela "El Roble" - Evolución Temporal             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌────────────────────────────────────────────────────────┐ ║
║  │                                                        │ ║
║  │         [IMAGEN SATELITAL DEL MES]                    │ ║
║  │                                                        │ ║
║  │   🌟 Enero 2024        NDVI: 0.756 ✅ Muy Buena Salud │ ║
║  │                                     ☁️ Nubosidad: 12% │ ║
║  └────────────────────────────────────────────────────────┘ ║
║                                                              ║
║  ┌─────────┬─────────┬──────────┬──────────┐               ║
║  │📅 Enero │🌿 0.756 │✅ Muy    │📈 +8.5%  │               ║
║  │   2024  │         │  Buena   │ vs ant.  │               ║
║  └─────────┴─────────┴──────────┴──────────┘               ║
║                                                              ║
║  ✅ Muy Buena Salud • 💧 Humedad Adecuada • 🌡️ 25.5°C      ║
║                                                              ║
║  [🌿 NDVI]  [💧 NDMI]  [🌱 SAVI]  ← Selector de Índice     ║
║                                                              ║
║  [⏮️] [◀️] [▶️ PLAY] [▶️] [⏭️]  ━━━●━━━━━  [3 / 12]       ║
║   │    │      │      │    │        │           │            ║
║   │    │      │      │    │        │           └─ Contador  ║
║   │    │      │      │    │        └─ Slider temporal       ║
║   │    │      │      │    └─ Siguiente                      ║
║   │    │      │      └─ Anterior                            ║
║   │    │      └─ Reproducir/Pausar                          ║
║   │    └─ Primer frame                                      ║
║   └─ Último frame                                           ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🎯 Elementos Clave

### 1. Canvas de Visualización

- **Imagen Satelital**: La imagen real capturada por satélite
- **Overlay Inferior**: Información contextual del mes
  - Período (Enero 2024)
  - Valor del índice (NDVI: 0.756)
  - Estado de salud (✅ Muy Buena Salud)
  - Nubosidad (☁️ 12%)

### 2. Panel de Metadata (4 Indicadores)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 📅 Período   │  │ 🌿 Índice    │  │ ✅ Estado    │  │ 📈 Tendencia │
│  Enero 2024  │  │    0.756     │  │  Muy Buena   │  │   +8.5%      │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### 3. Resumen Ejecutivo

```
✅ Muy Buena Salud • 💧 Humedad Adecuada • 🌡️ 25.5°C • 🌧️ 120mm
```

Lenguaje simple para que cualquier agricultor entienda.

### 4. Selector de Índice

```
[🌿 NDVI activo]  [💧 NDMI]  [🌱 SAVI]
```

Click para cambiar entre índices sin recargar.

### 5. Controles de Reproducción

```
⏮️  = Ir al primer mes (Home)
◀️  = Mes anterior (← Flecha Izquierda)
▶️  = Reproducir/Pausar (Espacio)
▶️  = Mes siguiente (→ Flecha Derecha)
⏭️  = Ir al último mes (End)
━━━●━━━━━ = Slider para navegar directamente
3 / 12 = Contador (Mes actual / Total meses)
```

---

## 🎨 Estados Visuales

### Clasificación por Color (NDVI)

| Valor      | Color     | Icono | Estado               | Descripción                    |
|------------|-----------|-------|----------------------|--------------------------------|
| ≥ 0.85     | 🟢 Verde  | 🌟    | Vegetación Excelente | Muy densa y saludable          |
| ≥ 0.75     | 🟢 Verde  | ✅    | Muy Buena Salud      | Vigorosa y productiva          |
| ≥ 0.60     | 🔵 Azul   | 👍    | Buena Salud          | Saludable con buen desarrollo  |
| ≥ 0.40     | 🟡 Amarillo| ⚠️   | Salud Moderada       | En desarrollo o estrés leve    |
| < 0.40     | 🔴 Rojo   | 🔴    | Estrés Detectado     | Vegetación escasa o estrés severo|

### Tendencias

| Cambio vs Anterior | Icono | Etiqueta   | Color |
|-------------------|-------|------------|-------|
| > +2%             | 📈    | Mejora     | Verde |
| -2% a +2%         | ➡️    | Estable    | Gris  |
| < -2%             | 📉    | Deterioro  | Rojo  |

---

## ⌨️ Atajos de Teclado

| Tecla            | Acción                    |
|------------------|---------------------------|
| `Espacio`        | Play / Pause              |
| `Enter`          | Play / Pause              |
| `← Izquierda`    | Mes anterior              |
| `→ Derecha`      | Mes siguiente             |
| `Home`           | Primer mes                |
| `End`            | Último mes                |
| Click en Canvas  | Play / Pause              |

---

## 📱 Responsive Design

### Desktop (≥ 992px)

- Canvas: 1200x600px
- Controles horizontales
- Metadata en 4 columnas

### Tablet (768px - 991px)

- Canvas: 100% ancho, 400px alto
- Controles compactos
- Metadata en 2 columnas

### Mobile (< 768px)

- Canvas: 100% ancho, 350px alto
- Controles apilados verticalmente
- Metadata en 1 columna
- Botones más grandes (táctil)

---

## 🔄 Flujo de Reproducción

```
Usuario clickea "Play"
        ↓
    Frame 1 (Enero 2024)
        ↓
    Espera 1.5 seg
        ↓
    Frame 2 (Febrero 2024)
        ↓
    Espera 1.5 seg
        ↓
    Frame 3 (Marzo 2024)
        ↓
    ...
        ↓
    Frame 12 (Diciembre 2024)
        ↓
    Reinicia desde Frame 1
```

Durante la reproducción:
- ✅ Imágenes se precargan automáticamente
- ✅ Metadata se actualiza en tiempo real
- ✅ Usuario puede pausar en cualquier momento
- ✅ Usuario puede usar slider para saltar frames

---

## 💡 Casos de Uso

### Caso 1: Agricultor revisa su parcela

> "Quiero ver cómo ha evolucionado mi cultivo en el último año"

1. Accede al detalle de su parcela
2. Click en "Timeline Visual"
3. Click en "Play"
4. Observa el cambio mes a mes
5. Identifica visualmente períodos de estrés (🔴) o salud (🌟)

### Caso 2: Ingeniero agrónomo analiza tendencias

> "Necesito identificar cuándo empezó el estrés hídrico"

1. Accede al timeline
2. Cambia a índice NDMI (💧 Humedad)
3. Navega mes a mes con flechas
4. Observa el panel de tendencias (📈/📉)
5. Identifica el mes donde cambió de "Adecuada" a "Estrés Hídrico"

### Caso 3: Cliente sin conocimientos técnicos

> "No entiendo los números, solo quiero saber si mi parcela está bien"

1. Accede al timeline
2. Lee el resumen simple:
   - ✅ Muy Buena Salud ← Está bien
   - 💧 Humedad Adecuada ← No falta agua
   - 🌡️ 25.5°C ← Temperatura normal
3. Ve colores: Verde = Bien, Rojo = Mal
4. Entiende sin leer números técnicos

---

## 🚀 Ventajas sobre el Informe PDF

| Característica          | Informe PDF | Timeline Visual |
|-------------------------|-------------|-----------------|
| **Comprensión**         | Técnica     | Intuitiva ✅    |
| **Visualización**       | Gráficos    | Imágenes reales ✅|
| **Interactividad**      | ❌ No       | ✅ Sí           |
| **Comparación temporal**| Estática    | Dinámica ✅     |
| **Mobile-friendly**     | Regular     | Excelente ✅    |
| **Wow Factor**          | Bajo        | Muy Alto ✅     |

Ambos sistemas coexisten:
- **PDF**: Análisis técnico detallado para reportes formales
- **Timeline**: Experiencia visual para comprensión rápida

---

## 📖 Siguiente Paso

**¡Prueba el Timeline ahora!**

```bash
# 1. Inicia el servidor
python manage.py runserver

# 2. Accede a una parcela
http://localhost:8000/parcelas/1/

# 3. Click en "🎬 Timeline Visual"

# 4. ¡Disfruta la experiencia cinematográfica! 🎉
```

---

**Desarrollado por AgroTech Team**  
Diciembre 2025
