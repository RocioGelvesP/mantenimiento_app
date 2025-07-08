# Documentación: Programación Automática de Mantenimientos Futuros

## Descripción del Problema

Anteriormente, al programar un mantenimiento con una frecuencia específica (ej: BIMESTRAL), solo se creaba un mantenimiento programado. Los mantenimientos futuros debían ser creados manualmente, lo que causaba problemas de planificación y seguimiento.

## Solución Implementada

Se ha implementado una funcionalidad que **automáticamente crea múltiples mantenimientos futuros** basados en la frecuencia especificada al programar un mantenimiento **de tipo PREVENTIVO**.

### Características Principales

1. **Programación Solo para el Año en Curso**: Los mantenimientos se programan únicamente hasta el 31 de diciembre del año actual.

2. **Evita Días No Laborables**: 
   - **Domingos**: Se mueven automáticamente al siguiente día hábil
   - **Festivos Colombianos**: Se utilizan las fechas oficiales de festivos de Colombia

3. **Frecuencias Soportadas**:
   - Diario (1 día)
   - Semanal (7 días)
   - Quincenal (15 días)
   - Mensual (30 días)
   - **Bimestral (60 días)**
   - Trimestral (90 días)
   - Semestral (180 días)
   - Anual (365 días)

4. **Evita Duplicados**: No se crean mantenimientos si ya existe uno para la misma fecha, equipo y tipo de mantenimiento.

5. **Solo para Mantenimientos Preventivos**: La programación automática de mantenimientos futuros solo se aplica a mantenimientos de tipo "Preventivo". Los otros tipos (Correctivo, Predictivo, etc.) se crean de uno en uno.

## Cómo Funciona

### 1. Al Programar un Mantenimiento

Cuando se programa un mantenimiento **de tipo PREVENTIVO** con frecuencia "BIMESTRAL" para el equipo EM-075:

1. Se crea el mantenimiento inicial con la fecha especificada
2. Se calcula automáticamente la fecha del próximo mantenimiento
3. Se crean automáticamente todos los mantenimientos futuros para el año en curso

**Nota**: Para mantenimientos de otros tipos (Correctivo, Predictivo, etc.), solo se crea el mantenimiento individual sin programación automática de futuros.

### 2. Ejemplo: Mantenimiento BIMESTRAL

Si se programa un mantenimiento BIMESTRAL para el 15 de enero de 2025:

- **Mantenimiento inicial**: 15 de enero de 2025
- **Mantenimientos futuros creados automáticamente**:
  - 16 de marzo de 2025 (si el 15 cae en domingo o festivo, se mueve al siguiente día hábil)
  - 15 de mayo de 2025
  - 14 de julio de 2025
  - 12 de septiembre de 2025
  - 11 de noviembre de 2025

### 3. Mensaje de Confirmación

Al programar exitosamente un mantenimiento preventivo, se muestra un mensaje como:
```
Mantenimiento #58 para el equipo EM-075 programado correctamente. 
Se crearon 5 mantenimientos preventivos futuros adicionales para el año 2025.
```

Para otros tipos de mantenimiento, el mensaje será:
```
Mantenimiento #58 para el equipo EM-075 programado correctamente.
```

## Archivos Modificados

### `routes/maintenance.py`

1. **Nueva función**: `crear_mantenimientos_futuros(mantenimiento_base)`
   - Crea mantenimientos futuros basados en la frecuencia
   - Evita domingos y festivos
   - Solo programa para el año en curso

2. **Función modificada**: `programar()`
   - Llama automáticamente a `crear_mantenimientos_futuros()`
   - Muestra mensaje informativo sobre mantenimientos creados

## Scripts de Prueba

### `probar_programacion_futura.py`
Script para probar la nueva funcionalidad:
```bash
python probar_programacion_futura.py
```

### `limpiar_mantenimientos_prueba.py`
Script para limpiar mantenimientos de prueba:
```bash
python limpiar_mantenimientos_prueba.py
```

## Dependencias

- **holidays**: Para obtener festivos colombianos
- Ya incluida en `requirements.txt`

## Beneficios

1. **Automatización**: No es necesario crear manualmente cada mantenimiento futuro
2. **Consistencia**: Todos los mantenimientos mantienen la misma información (técnico, repuestos, etc.)
3. **Planificación**: Facilita la planificación anual de mantenimientos
4. **Cumplimiento**: Asegura que no se pierdan mantenimientos programados
5. **Flexibilidad**: Respeta días no laborables automáticamente

## Consideraciones

- Los mantenimientos se crean solo para el año en curso
- Se evitan automáticamente domingos y festivos colombianos
- No se duplican mantenimientos existentes
- La funcionalidad se activa solo cuando se especifica una frecuencia válida

## Próximos Pasos

Para el año siguiente, se puede implementar una funcionalidad similar a `programar_mantenimientos_nuevo_ano()` que ya existe, pero adaptada para crear mantenimientos futuros basados en frecuencias. 