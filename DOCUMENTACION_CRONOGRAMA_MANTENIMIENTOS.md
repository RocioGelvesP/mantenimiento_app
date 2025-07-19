# Documentación: Cronograma de Mantenimientos por Equipo

## Descripción

Se ha implementado una nueva funcionalidad que permite generar PDFs de cronograma de mantenimientos por equipo para el año en curso, similar al formato del documento mostrado en la imagen de referencia. Esta funcionalidad facilita la planificación y seguimiento de mantenimientos preventivos.

## Características Principales

### 1. Generación de Cronograma Individual por Equipo
- **Formato**: PDF en orientación landscape (apaisado)
- **Contenido**: Cronograma anual completo con todos los mantenimientos del equipo
- **Estructura**: Similar al documento de referencia con tabla de meses/semanas
- **Encabezado**: Incluye información de la empresa y datos del equipo en todas las páginas

### 2. Generación de Cronograma Combinado
- **Formato**: PDF combinado con todos los equipos que tienen mantenimientos
- **Estructura**: Un cronograma por página para cada equipo
- **Encabezado**: Se repite en todas las páginas con información de la empresa

### 3. Acceso desde la Interfaz Web
- **Botón "Cronograma Anual"**: En la lista de mantenimientos (para todos los equipos)
- **Botón de calendario**: En cada fila de mantenimiento (para equipo específico)
- **Botón en vista individual**: En la página de ver mantenimiento

## Funcionalidades Implementadas

### Archivos Modificados

#### 1. `utils.py`
- **`create_reportlab_pdf_maintenance_schedule()`**: Genera PDF de cronograma para un equipo
- **`create_reportlab_pdf_all_equipment_schedules()`**: Genera PDF combinado para todos los equipos
- **`generar_y_enviar_pdf_cronograma()`**: Función auxiliar para enviar PDFs
- **`draw_encabezado_cronograma()`**: **NUEVA** - Dibuja el encabezado con información de la empresa

#### 2. `routes/maintenance.py`
- **`cronograma_equipo(codigo)`**: Ruta para generar cronograma de equipo específico
- **`cronograma_equipo_year(codigo, year)`**: Ruta para año específico
- **Soporte para 'todos'**: Genera cronograma combinado cuando codigo='todos'

#### 3. `templates/maintenance/lista.html`
- **Botón "Cronograma Anual"**: En la sección de botones principales
- **Botón de calendario**: En cada fila de mantenimiento

#### 4. `templates/maintenance/ver.html`
- **Botón "Cronograma del Equipo"**: En la vista individual de mantenimiento

## Estructura del Encabezado

### 🏢 **Información de la Empresa (4 Columnas - Columnas Ultra Compactas)**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│[L]│INR INVERSIONES│  CRONOGRAMA DE MANTENIMIENTO  │  Código │
│   │REINOSO Y CIA. │  PREVENTIVO MÁQUINAS Y/O      │  62-MT- │
│   │LTDA.          │  EQUIPOS                      │  SE099 3│
│   │               │                               │  Edición│
│   │               │                               │  14/ene/│
│   │               │                               │    25   │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│ Código máquina/equipo │        Nombre máquina o equipo        │ Aprobó: Jefe │
│                       │                                         │ de Mantenim. │
│      SE-099           │    EXTRACTOR DE POLVO DE CAUCHO        │      ✓      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Elementos del Encabezado**
- **Logo**: Imagen desde `static/logo.png` (55×35 puntos) con fallback a óvalo rojo con "INR"
- **Empresa**: "INR INVERSIONES REINOSO Y CIA. LTDA." en dos líneas
- **Título (Columna 3)**: Dividida en dos partes:
  - **Mitad superior**: "CRONOGRAMA DE MANTENIMIENTO PREVENTIVO MÁQUINAS Y/O EQUIPOS" (una sola línea)
  - **Mitad inferior**: Información del equipo y aprobación
    - **Columna izquierda**: Código y nombre del equipo
    - **Columna derecha**: "Aprobó: Jefe de Mantenimiento" con checkmark (✓)
- **Código del Documento**: "62-MT-[CODIGO] 3" (ej: 62-MT-SE099 3)
- **Edición**: "14/ene/[AÑO]" (ej: 14/ene/25)

### **Colores y Estilo**
- **Estructura**: 4 columnas con anchos personalizados [30, 80, 634, 40] puntos
- **Borde**: Negro fino alrededor del encabezado completo
- **Líneas verticales**: Separación entre columnas
- **Texto**: Negro sobre fondo blanco
- **Fuente**: Helvetica-Bold para títulos, Helvetica para datos
- **Posición**: Se repite en todas las páginas del documento
- **Logo**: Carga automática desde `static/logo.png` con fallback a óvalo rojo con "INR"

### **Información del Equipo Integrada**
- **Integrada en la columna 3** del encabezado (mitad inferior):
  - **Código del equipo**: Se muestra en la columna izquierda
  - **Nombre del equipo**: Se muestra en la columna izquierda (dividido en dos líneas si es muy largo)
  - **Aprobación**: "Aprobó: Jefe de Mantenimiento" con checkmark (✓) en la columna derecha
- **Líneas de separación**: Horizontal para dividir la columna 3, vertical para separar las dos columnas internas
- **Fuentes**: Helvetica-Bold (8pt) para etiquetas, Helvetica (7-8pt) para datos

## Estructura del Cronograma

### Información del Equipo (Simplificada)
```
Ubicación: [Ubicación del equipo]                    Año: 2025
Proceso: [Proceso del equipo]                        Centro de Costos: [Centro de costos]
```

### Tabla de Cronograma
- **Columnas**: No., INSTRUCCIONES, FREC., [12 meses × 4 semanas]
- **Filas**: Cada servicio de mantenimiento como una fila separada
- **Marcadores**:
  - `I`: Inspección
  - `L`: Lubricación
  - `A`: Ajuste
  - `LZ`: Limpieza
  - `M`: Mantenimiento general
  - `ok`: Ejecutado/completado

### Leyenda
```
PROG: Programado    EJEC: Ejecutado
I: Inspección       L: Lubricación
A: Ajuste           LZ: Limpieza
Frecuencia: S: Semanal, M: Mensual, BI: Bimensual, TR: Trimestral, SE: Semestral, AN: Anual
RP: Reprogramado    ok: Realizado
```

### Tabla de Seguimiento
- **Mantenimiento ejecutado**: Por mes y total
- **Mantenimiento Programado**: Por mes y total
- **Porcentaje de cumplimiento**: Por mes y total

## Cómo Usar la Funcionalidad

### 1. Desde la Lista de Mantenimientos

#### Para Todos los Equipos:
1. Ir a **Mantenimientos** → **Lista de Mantenimientos**
2. Hacer clic en el botón **"Cronograma Anual"** (amarillo con icono de calendario)
3. Se descargará automáticamente un PDF con cronogramas de todos los equipos

#### Para un Equipo Específico:
1. En la lista de mantenimientos, buscar el mantenimiento del equipo deseado
2. Hacer clic en el botón **calendario** (amarillo) en la columna de acciones
3. Se descargará el cronograma específico de ese equipo

### 2. Desde la Vista Individual de Mantenimiento

1. Hacer clic en **"Ver"** en cualquier mantenimiento
2. En la parte inferior de la página, hacer clic en **"Cronograma del Equipo"**
3. Se descargará el cronograma del equipo correspondiente

### 3. URLs Directas

- **Cronograma del año actual**: `/maintenance/cronograma-equipo/EM-075`
- **Cronograma de año específico**: `/maintenance/cronograma-equipo/EM-075/2025`
- **Cronograma de todos los equipos**: `/maintenance/cronograma-equipo/todos`

## Características Técnicas

### Generación de PDF
- **Librería**: ReportLab
- **Orientación**: Landscape (apaisado) para mejor visualización
- **Tamaño**: A4
- **Fuentes**: Helvetica para mejor compatibilidad
- **Colores**: Esquema de colores consistente con la aplicación
- **Encabezado**: Se repite automáticamente en todas las páginas

### Cálculo de Semanas
- **Semana 1**: Días 1-7 del mes
- **Semana 2**: Días 8-14 del mes
- **Semana 3**: Días 15-21 del mes
- **Semana 4**: Días 22-28/29/30/31 del mes

### Detección de Actividades
- **Inspección**: Contiene "inspec" o "revis" en el nombre del servicio
- **Lubricación**: Contiene "lubric" o "lubricación" en el nombre del servicio
- **Ajuste**: Contiene "ajust" en el nombre del servicio
- **Limpieza**: Contiene "limpi" en el nombre del servicio
- **General**: Cualquier otro tipo de mantenimiento

### Generación del Código del Documento
- **Formato**: `62-MT-[CODIGO] 3`
- **Ejemplo**: Para equipo EM-075 → `62-MT-EM075 3`
- **Cronograma combinado**: `62-MT-000 3`

## Script de Prueba

Se incluye el script `probar_cronograma.py` para verificar la funcionalidad:

```bash
python probar_cronograma.py
```

Este script:
- Muestra estadísticas de mantenimientos programados
- Prueba la generación del encabezado
- Prueba la generación de cronograma individual
- Prueba la generación de cronograma combinado
- Genera archivos PDF de prueba para verificación

## Beneficios

### 1. Planificación Visual
- Vista clara de todos los mantenimientos del año
- Identificación rápida de frecuencias y tipos de mantenimiento
- Seguimiento del cumplimiento por mes

### 2. Documentación Profesional
- Formato estándar similar al documento de referencia
- Encabezado corporativo con información de la empresa
- Información completa del equipo y mantenimientos
- Fácil impresión y archivo

### 3. Gestión de Mantenimientos
- Identificación de equipos sin mantenimientos programados
- Seguimiento de cumplimiento de mantenimientos
- Planificación de recursos y técnicos

### 4. Cumplimiento Normativo
- Documentación para auditorías
- Evidencia de planificación de mantenimientos
- Seguimiento de frecuencias establecidas
- Encabezado corporativo para identificación de documentos

## Consideraciones

### Limitaciones
- Solo incluye mantenimientos programados (no históricos)
- Requiere mantenimientos con fechas válidas
- El cálculo de semanas es aproximado (no considera semanas naturales)

### Mejoras Futuras
- Incluir mantenimientos históricos para comparación
- Agregar gráficos de cumplimiento
- Integrar con calendario de festivos
- Exportar a Excel con formato similar
- Personalizar colores del encabezado según la empresa

## Archivos Generados

### Nombres de Archivos
- **Equipo individual**: `cronograma_EM-075_2025.pdf`
- **Todos los equipos**: `cronograma_todos_equipos_2025.pdf`
- **Archivos de prueba**: `cronograma_prueba_*.pdf`

### Ubicación
- Los archivos se descargan automáticamente al navegador del usuario
- Los archivos de prueba se guardan en el directorio raíz del proyecto

## Soporte

Para reportar problemas o solicitar mejoras:
1. Verificar que existen mantenimientos programados para el año actual
2. Ejecutar el script de prueba para diagnosticar problemas
3. Revisar los logs de la aplicación para errores específicos
4. Contactar al administrador del sistema

---

**Nota**: Esta funcionalidad está diseñada para complementar el sistema de mantenimientos existente y facilitar la planificación y seguimiento de actividades de mantenimiento preventivo. El encabezado corporativo asegura que todos los documentos generados tengan una identidad visual consistente con la empresa. 

## 📐 **Configuración de Layout y Espaciado**

### **Márgenes del Documento**
- **Orientación**: Landscape (horizontal)
- **Tamaño**: A4
- **Margen superior**: 5 cm (reducido para encabezado más arriba)
- **Margen inferior**: 2.5 cm (para el footer)
- **Margen izquierdo**: 1 cm
- **Margen derecho**: 1 cm

### **Espaciado del Encabezado**
- **Altura del encabezado principal**: 55 puntos
- **Separación entre encabezado y tabla**: 20 puntos (reducido)
- **Altura de la tabla de información**: 20 puntos
- **Espaciador adicional en contenido**: 10 puntos (reducido)
- **Posición Y del encabezado**: +15 puntos desde el margen superior (más arriba)

### **Estructura Visual Mejorada (Columnas Ultra Compactas)**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│[L]│INR INVERSIONES│  CRONOGRAMA DE MANTENIMIENTO  │  Código │
│   │REINOSO Y CIA. │  PREVENTIVO MÁQUINAS Y/O      │  62-MT- │
│   │LTDA.          │  EQUIPOS                      │  SE099 3│
│   │               │  ──────────────────────────── │  Edición│
│   │               │  Código: │ Aprobó:            │  14/ene/│
│   │               │  SE-099  │ Jefe de            │    25   │
│   │               │  Nombre: │ Mantenimiento      │         │
│   │               │  EXTRACTOR│ ✓                 │         │
│   │               │  DE POLVO│                    │         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    [ESPACIO DE 20 PUNTOS]
┌─────────────────────────────────────────────────────────────────────────────┐
│ Ubicación: ACABADOS  │  Proceso: PRENSADOS  │  Año: 2025  │  Centro Costos: N/A │
└─────────────────────────────────────────────────────────────────────────────┘
                                    [ESPACIO DE 15 PUNTOS]
┌─────────────────────────────────────────────────────────────────────────────┐
│ No. │ INSTRUCCIONES │ FREC. │ ENE1 │ ENE2 │ ENE3 │ ENE4 │ FEB1 │ FEB2 │ ... │
│     │               │       │ PROG │ PROG │ PROG │ PROG │ PROG │ PROG │     │
│     │               │       │ EJEC │ EJEC │ EJEC │ EJEC │ EJEC │ EJEC │     │
└─────────────────────────────────────────────────────────────────────────────┘
``` 