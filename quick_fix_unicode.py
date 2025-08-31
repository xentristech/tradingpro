#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick Fix para quitar todos los emojis Unicode de los archivos principales
"""
import os
import re

def fix_unicode_in_file(file_path):
    """Reemplaza emojis Unicode por texto simple"""
    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazos de emojis por texto
        replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '🚨': '[ALERT]',
            '📊': '[INFO]',
            '📈': '[STATS]',
            '🛡️': '[PROTECTION]',
            '\u2705': '[OK]',
            '\u274c': '[ERROR]',
            '\u26a0': '[WARNING]',
            '\u1f6a8': '[ALERT]'
        }
        
        original_content = content
        for emoji, replacement in replacements.items():
            content = content.replace(emoji, replacement)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed: {file_path}")
        else:
            print(f"- No changes needed: {file_path}")
    
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")

if __name__ == "__main__":
    files_to_fix = [
        "src/broker/mt5_connection.py",
        "src/signals/advanced_signal_generator.py", 
    ]
    
    print("Fixing Unicode emojis in key files...")
    for file_path in files_to_fix:
        fix_unicode_in_file(file_path)
    
    print("Done!")