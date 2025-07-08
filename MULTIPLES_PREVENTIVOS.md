# Múltiples Mantenimientos Preventivos

## Descripción

Se ha implementado la funcionalidad para permitir que un usuario pueda programar múltiples mantenimientos preventivos para el mismo equipo, siempre que tengan diferentes servicios o frecuencias.

## Cambios Implementados

### 1. Modificación de la Validación Backend

#### Archivo: `routes/maintenance.py`

**Función `verificar_preventivo`:**
- Ahora acepta parámetros opcionales `servicio` y `frecuencia`
- Si se especifican ambos parámetros, busca mantenimientos que coincidan exactamente
- Si no se especifican, muestra todos los mantenimientos preventivos del equipo
- Retorna información más detallada incluyendo servicio y frecuencia

**Función `crear_mantenimientos_futuros`:**
- Modificada para considerar el campo `servicio` al verificar duplicados
- Ahora evita crear mantenimientos futuros solo si existe uno con el mismo equipo, fecha, tipo y servicio

**Función `programar_mantenimientos_nuevo_ano`:**
- Modificada para considerar el campo `servicio` al verificar duplicados

### 2. Modificación de la Validación Frontend

#### Archivo: `templates/maintenance/programar.html`

**Función `verificarPreventivoExistente`:**
- Ahora acepta parámetros opcionales `servicio` y `frecuencia`
- Construye la URL con parámetros de consulta cuando se especifican

**Función `validarCombinacionEquipoTipo`:**
- Modificada para validar específicamente cuando se han seleccionado servicio y frecuencia
- Muestra mensajes más específicos sobre qué servicio/frecuencia ya existe
- Permite continuar si el servicio o frecuencia son diferentes

**Función `filtrarEquipos`:**
- Simplificada para cargar todos los equipos (ya no filtra equipos con preventivos)
- Permite seleccionar cualquier equipo para programar múltiples mantenimientos

**Event Listeners:**
- Agregados listeners para los campos `servicio` y `frecuencia`
- La validación se ejecuta automáticamente cuando cambian estos campos

## Cómo Funciona

### Antes (Comportamiento Anterior)
- Solo se permitía UN mantenimiento preventivo por equipo por año
- Si un equipo ya tenía un mantenimiento preventivo, no se podía programar otro
- La validación era muy restrictiva

### Ahora (Nuevo Comportamiento)
- Se permiten MÚLTIPLES mantenimientos preventivos por equipo
- La validación se basa en la combinación: **Equipo + Servicio + Frecuencia**
- Se pueden programar diferentes tipos de mantenimientos preventivos:
  - Lubricación (Bimestral)
  - Limpieza (Mensual)
  - Revisión técnica (Trimestral)
  - Calibración (Semestral)
  - etc.

### Ejemplo de Uso

1. **Programar Lubricación Bimestral:**
   - Equipo: EM-075
   - Servicio: Lubricación general
   - Frecuencia: Bimestral
   - ✅ Se permite

2. **Programar Limpieza Mensual (mismo equipo):**
   - Equipo: EM-075
   - Servicio: Limpieza general
   - Frecuencia: Mensual
   - ✅ Se permite (diferente servicio y frecuencia)

3. **Intentar programar otra Lubricación Bimestral:**
   - Equipo: EM-075
   - Servicio: Lubricación general
   - Frecuencia: Bimestral
   - ❌ Se bloquea (misma combinación)

## Validaciones

### Validaciones que se Mantienen
- No se pueden crear mantenimientos con la misma combinación exacta (equipo + servicio + frecuencia)
- Se evitan duplicados en la creación de mantenimientos futuros
- Se respetan las fechas y horarios

### Validaciones que se Relajaron
- Se permite múltiples mantenimientos preventivos por equipo
- Se permite programar mantenimientos en equipos que ya tienen otros preventivos

## Mensajes de Usuario

### Mensajes Informativos
- "El equipo EM-075 ya tiene mantenimiento(s) preventivo(s) programado(s) para el año 2025. Selecciona un servicio y frecuencia diferentes para continuar."

### Mensajes de Error
- "El equipo EM-075 ya tiene un mantenimiento preventivo con el servicio 'Lubricación general' y frecuencia 'Bimestral' programado para el año 2025. Por favor, selecciona un servicio o frecuencia diferente."

## Pruebas

### Script de Prueba
Se incluye el archivo `probar_multiples_preventivos.py` que:
- Crea múltiples mantenimientos preventivos para el mismo equipo
- Verifica que no se creen duplicados exactos
- Prueba la creación de mantenimientos futuros
- Valida el comportamiento esperado

### Ejecutar Pruebas
```bash
python probar_multiples_preventivos.py
```

## Beneficios

1. **Flexibilidad:** Permite programar diferentes tipos de mantenimientos preventivos
2. **Organización:** Cada tipo de mantenimiento tiene su propia frecuencia
3. **Trazabilidad:** Se mantiene el control de cada tipo de mantenimiento por separado
4. **Eficiencia:** No se duplican mantenimientos innecesariamente
5. **Usabilidad:** Interfaz más intuitiva con validaciones específicas

## Consideraciones Técnicas

### Base de Datos
- No se requieren cambios en la estructura de la base de datos
- Se aprovecha la validación existente agregando el campo `servicio`

### Rendimiento
- Las consultas se mantienen eficientes
- Se agregaron índices implícitos en las validaciones

### Compatibilidad
- Los cambios son compatibles con mantenimientos existentes
- No se afectan los mantenimientos correctivos o predictivos

## Casos de Uso Comunes

1. **Mantenimiento de Maquinaria Industrial:**
   - Lubricación semanal
   - Limpieza diaria
   - Revisión técnica mensual
   - Calibración trimestral

2. **Mantenimiento de Equipos de Oficina:**
   - Limpieza semanal
   - Revisión técnica mensual
   - Actualización de software trimestral

3. **Mantenimiento de Vehículos:**
   - Revisión de aceite mensual
   - Cambio de filtros trimestral
   - Revisión completa semestral 