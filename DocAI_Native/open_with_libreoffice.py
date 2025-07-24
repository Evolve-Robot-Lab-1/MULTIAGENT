#!/usr/bin/env python3
"""
Simple script to test opening documents with LibreOffice
"""

import sys
import subprocess
import platform
from pathlib import Path

def open_with_libreoffice(file_path):
    """Open a document with LibreOffice"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    system = platform.system()
    
    try:
        if system == "Linux":
            # Try different LibreOffice commands
            commands = ['libreoffice', 'soffice', '/usr/bin/libreoffice', '/usr/bin/soffice']
            for cmd in commands:
                try:
                    subprocess.run([cmd, '--view', str(file_path)])
                    print(f"Opened with {cmd}")
                    return True
                except FileNotFoundError:
                    continue
            
        elif system == "Windows":
            # Common LibreOffice paths on Windows
            paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]
            for path in paths:
                if Path(path).exists():
                    subprocess.run([path, '--view', str(file_path)])
                    print(f"Opened with {path}")
                    return True
                    
        elif system == "Darwin":  # macOS
            subprocess.run(['open', '-a', 'LibreOffice', str(file_path)])
            print("Opened with LibreOffice on macOS")
            return True
            
    except Exception as e:
        print(f"Error opening with LibreOffice: {e}")
        
    # Fallback - open with system default
    try:
        if system == "Linux":
            subprocess.run(['xdg-open', str(file_path)])
        elif system == "Windows":
            subprocess.run(['start', '', str(file_path)], shell=True)
        elif system == "Darwin":
            subprocess.run(['open', str(file_path)])
        print("Opened with system default application")
        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python open_with_libreoffice.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    success = open_with_libreoffice(file_path)
    sys.exit(0 if success else 1)