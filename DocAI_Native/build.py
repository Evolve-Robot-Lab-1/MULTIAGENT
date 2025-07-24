#!/usr/bin/env python3
"""
Build script for DocAI Native
Creates executable using PyInstaller
"""

import PyInstaller.__main__
import shutil
import sys
from pathlib import Path

def clean_build():
    """Clean previous builds"""
    build_dirs = ['dist', 'build', '__pycache__']
    for dir_name in build_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"Cleaned {dir_name}/")

def build_executable():
    """Build executable with PyInstaller"""
    
    print("Building DocAI Native executable...")
    
    # PyInstaller arguments
    args = [
        'main.py',
        '--name=DurgaAI-Native',
        '--onefile',
        '--windowed',
        '--icon=frontend/static/assets/Durga.png',
        '--add-data=frontend:frontend',
        '--add-data=config.py:.',
        '--hidden-import=uno',
        '--hidden-import=flask',
        '--hidden-import=webview',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build',
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("Build complete! Check dist/ folder")

def main():
    """Main build function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--clean':
        clean_build()
        return
    
    # Clean and build
    clean_build()
    
    try:
        build_executable()
        print("\n✅ Build successful!")
        print("📁 Executable: dist/DurgaAI-Native")
        print("🚀 Ready to ship!")
        
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()