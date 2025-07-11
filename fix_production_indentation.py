#!/usr/bin/env python3
"""
Script para corregir el error de indentación específico en producción
Error: IndentationError: expected an indented block after 'with' statement on line 949
"""

import os
import re

def fix_equipment_indentation():
    """Corrige el error de indentación en equipment.py"""
    
    file_path = '/app/routes/equipment.py'
    
    if not os.path.exists(file_path):
        print(f"Archivo {file_path} no encontrado")
        return False
    
    print(f"Corrigiendo {file_path}...")
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Archivo tiene {len(lines)} líneas")
    
    # Buscar el problema específico
    fixed = False
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Buscar líneas con 'with' que puedan tener problemas
        if 'with' in line and 'as' in line and line.strip().endswith(':'):
            print(f"Encontrado 'with' en línea {line_num}: {line.strip()}")
            
            # Verificar la siguiente línea
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_line_num = line_num + 1
                
                # Si la siguiente línea no está indentada y contiene 'f.write(html)'
                if (next_line.strip() and 
                    not next_line.startswith('    ') and 
                    not next_line.startswith('\t') and
                    'f.write(html)' in next_line):
                    
                    print(f"PROBLEMA ENCONTRADO en línea {next_line_num}: {next_line.strip()}")
                    print(f"Corrigiendo indentación...")
                    
                    # Corregir la indentación
                    lines[i + 1] = '    ' + next_line.lstrip()
                    fixed = True
                    print(f"Línea {next_line_num} corregida")
                
                # También verificar si hay líneas sin indentar después de 'with'
                elif (next_line.strip() and 
                      not next_line.startswith('    ') and 
                      not next_line.startswith('\t') and
                      not next_line.strip().startswith('#')):
                    
                    print(f"Línea {next_line_num} sin indentar después de 'with': {next_line.strip()}")
                    print(f"Corrigiendo indentación...")
                    
                    # Corregir la indentación
                    lines[i + 1] = '    ' + next_line.lstrip()
                    fixed = True
                    print(f"Línea {next_line_num} corregida")
    
    if fixed:
        # Crear backup
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Backup creado en {backup_path}")
        
        # Guardar el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"Archivo {file_path} corregido exitosamente")
        return True
    else:
        print("No se encontraron problemas de indentación para corregir")
        return False

def verify_syntax():
    """Verifica la sintaxis del archivo Python"""
    try:
        import py_compile
        py_compile.compile('/app/routes/equipment.py', doraise=True)
        print("✓ Sintaxis del archivo verificada correctamente")
        return True
    except Exception as e:
        print(f"✗ Error de sintaxis: {e}")
        return False

def main():
    """Función principal"""
    print("=== Corrección de Error de Indentación en Producción ===")
    
    # Corregir el archivo
    if fix_equipment_indentation():
        print("\n=== Verificando sintaxis ===")
        if verify_syntax():
            print("\n✓ Corrección completada exitosamente")
            print("La aplicación debería poder iniciar correctamente ahora")
        else:
            print("\n✗ Aún hay errores de sintaxis")
    else:
        print("\nNo se realizaron cambios")

if __name__ == "__main__":
    main() 