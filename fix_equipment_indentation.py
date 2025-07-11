#!/usr/bin/env python3
"""
Script para buscar y corregir errores de indentación en equipment.py
"""

import os
import re

def find_and_fix_indentation_error(file_path):
    """Busca y corrige errores de indentación en el archivo"""
    
    if not os.path.exists(file_path):
        print(f"Archivo {file_path} no encontrado")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Archivo {file_path} tiene {len(lines)} líneas")
    
    # Buscar patrones problemáticos
    problematic_patterns = [
        (r'with\s+.*open\s*\(.*\)\s*as\s+\w+:', 'with open statement'),
        (r'with\s+.*write\s*\(.*\)\s*as\s+\w+:', 'with write statement'),
        (r'f\.write\(html\)', 'f.write(html) call')
    ]
    
    found_issues = []
    
    for i, line in enumerate(lines, 1):
        for pattern, description in problematic_patterns:
            if re.search(pattern, line):
                found_issues.append((i, line.strip(), description))
    
    if found_issues:
        print("Problemas encontrados:")
        for line_num, line_content, description in found_issues:
            print(f"  Línea {line_num}: {description}")
            print(f"    Contenido: {line_content}")
        
        # Buscar específicamente el patrón problemático mencionado en el error
        for i, line in enumerate(lines, 1):
            if 'with' in line and 'as' in line:
                # Verificar si la siguiente línea no está indentada correctamente
                if i < len(lines):
                    next_line = lines[i]
                    if next_line.strip() and not next_line.startswith('    ') and not next_line.startswith('\t'):
                        print(f"  PROBLEMA ENCONTRADO: Línea {i} tiene 'with' pero línea {i+1} no está indentada")
                        print(f"    Línea {i}: {line.strip()}")
                        print(f"    Línea {i+1}: {next_line.strip()}")
                        
                        # Corregir la indentación
                        if next_line.strip():
                            lines[i] = '    ' + next_line.lstrip()
                            print(f"    CORREGIDO: Línea {i+1} ahora está indentada")
        
        # Guardar el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"Archivo {file_path} corregido")
        return True
    else:
        print("No se encontraron problemas de indentación")
        return False

def main():
    """Función principal"""
    print("Buscando errores de indentación en equipment.py...")
    
    # Buscar en diferentes ubicaciones posibles
    possible_paths = [
        'routes/equipment.py',
        '/app/routes/equipment.py',
        'equipment.py',
        'routes/equipment.py.bak',
        'routes/equipment.py.tmp'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"\nVerificando {path}...")
            if find_and_fix_indentation_error(path):
                print(f"Problema corregido en {path}")
            else:
                print(f"No se encontraron problemas en {path}")
        else:
            print(f"Archivo {path} no existe")

if __name__ == "__main__":
    main() 