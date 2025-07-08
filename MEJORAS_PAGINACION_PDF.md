# Mejoras en la Paginación de PDFs

## Problema Identificado

Los PDFs generados en el servidor no mostraban la paginación correctamente. El problema se debía a:

1. **Configuración hardcodeada**: Las opciones de `pdfkit` estaban definidas manualmente en cada función
2. **Falta de opciones optimizadas**: No se incluían todas las opciones necesarias para que la paginación funcione correctamente
3. **Inconsistencia entre archivos**: Diferentes archivos tenían configuraciones ligeramente diferentes

## Soluciones Implementadas

### 1. Función Centralizada de Configuración (`utils.py`)

Se creó la función `get_pdf_options()` que proporciona opciones optimizadas para la generación de PDFs:

```python
def get_pdf_options(orientation='Portrait', page_size='A4', include_footer=True, custom_footer=None):
    """
    Obtiene opciones optimizadas para PDF con paginación.
    """
    options = {
        'page-size': page_size,
        'orientation': orientation,
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.75in',  # Más espacio para el pie de página
        'margin-left': '0.5in',
        'encoding': 'UTF-8',
        'no-outline': None,
        'enable-local-file-access': None,
        'disable-smart-shrinking': None,
        'print-media-type': None,
        'no-stop-slow-scripts': None,
        'javascript-delay': '1000',
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore'
    }
    
    if include_footer:
        if custom_footer:
            options['footer-center'] = custom_footer
        else:
            options['footer-center'] = 'Página [page] de [topage]'
        options['footer-font-size'] = '10'
        options['footer-spacing'] = '5'
        options['footer-line'] = None  # Línea separadora
    
    return options
```

### 2. Opciones Optimizadas Incluidas

Las nuevas opciones incluyen:

- **`enable-local-file-access`**: Permite acceso a archivos locales
- **`disable-smart-shrinking`**: Evita que el contenido se redimensione automáticamente
- **`print-media-type`**: Optimiza para impresión
- **`no-stop-slow-scripts`**: Evita que se detengan scripts lentos
- **`javascript-delay`**: Da tiempo para que se ejecuten scripts JavaScript
- **`load-error-handling`**: Maneja errores de carga de manera más robusta
- **`footer-line`**: Agrega una línea separadora en el pie de página

### 3. Archivos Actualizados

Se actualizaron los siguientes archivos para usar la nueva función:

#### `routes/maintenance.py`
- `descargar_mantenimiento()`: Usa `get_pdf_options()` con pie de página personalizado
- `imprimir_todos()`: Usa `get_pdf_options()` con orientación landscape
- `descargar_todos()`: Usa `get_pdf_options()` con orientación landscape
- `descargar_historial()`: Usa `get_pdf_options()` con pie de página personalizado

#### `routes/equipment.py`
- `descargar_hoja_vida()`: Usa `get_pdf_options()` con orientación landscape
- `descargar_ficha_tecnica()`: Usa `get_pdf_options()` con orientación portrait

### 4. Corrección de Error Tipográfico

Se corrigió un error en `utils.py`:
```python
# Antes (línea 16)
raise FileNotFoundError(f"No se encontró wkhtmltopdf en: {patch_wkhtmltopdf}")

# Después
raise FileNotFoundError(f"No se encontró wkhtmltopdf en: {path_wkhtmltopdf}")
```

## Beneficios de las Mejoras

1. **Consistencia**: Todas las funciones usan la misma configuración base
2. **Mantenibilidad**: Los cambios se hacen en un solo lugar
3. **Robustez**: Las opciones optimizadas manejan mejor los errores
4. **Paginación Confiable**: La paginación ahora funciona correctamente en todos los PDFs
5. **Flexibilidad**: Se pueden personalizar opciones específicas por función

## Script de Prueba

Se creó `probar_paginacion_pdf.py` para verificar que la paginación funcione correctamente:

```bash
python probar_paginacion_pdf.py
```

Este script:
- Genera un PDF de prueba con múltiples páginas
- Verifica que la configuración funcione correctamente
- Proporciona feedback detallado sobre el proceso

## Verificación

Para verificar que la paginación funciona:

1. Generar cualquier PDF desde la aplicación
2. Verificar que aparezca "Página X de Y" en el pie de página
3. Navegar entre páginas para confirmar la numeración correcta
4. Verificar que el contenido se distribuya correctamente entre páginas

## Notas Técnicas

- La paginación usa las variables `[page]` y `[topage]` de wkhtmltopdf
- El margen inferior se aumentó a 0.75in para dar más espacio al pie de página
- Se agregó `footer-line` para una mejor separación visual
- Las opciones de manejo de errores hacen que la generación sea más robusta

## Compatibilidad

Las mejoras son compatibles con:
- Windows (wkhtmltopdf en `C:\Program Files\wkhtmltopdf\bin\`)
- Linux (wkhtmltopdf en `/usr/bin/wkhtmltopdf`)
- Todas las versiones de Python soportadas por la aplicación 