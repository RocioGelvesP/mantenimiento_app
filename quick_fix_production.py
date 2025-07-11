#!/usr/bin/env python3
"""
Script rápido para corregir el error de indentación en producción
"""

import os

def quick_fix():
    """Corrección rápida del error de indentación"""
    
    file_path = '/app/routes/equipment.py'
    
    if not os.path.exists(file_path):
        print(f"Archivo {file_path} no encontrado")
        return False
    
    print(f"Corrigiendo {file_path}...")
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar y corregir el patrón problemático
    # Buscar líneas que contengan 'f.write(html)' sin indentación después de 'with'
    lines = content.split('\n')
    fixed = False
    
    for i, line in enumerate(lines):
        # Si la línea contiene 'with' y termina con ':'
        if 'with' in line and line.strip().endswith(':'):
            # Verificar la siguiente línea
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Si la siguiente línea no está indentada y contiene 'f.write(html)'
                if ('f.write(html)' in next_line and 
                    next_line.strip() and 
                    not next_line.startswith('    ') and 
                    not next_line.startswith('\t')):
                    
                    print(f"Corrigiendo línea {i + 2}: {next_line.strip()}")
                    # Corregir la indentación
                    lines[i + 1] = '    ' + next_line.lstrip()
                    fixed = True
    
    if fixed:
        # Crear backup
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Backup creado en {backup_path}")
        
        # Guardar el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"Archivo {file_path} corregido exitosamente")
        return True
    else:
        print("No se encontró el patrón problemático específico")
        return False

if __name__ == "__main__":
    quick_fix() 