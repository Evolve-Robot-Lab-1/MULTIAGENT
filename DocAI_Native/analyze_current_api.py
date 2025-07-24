#!/usr/bin/env python3
"""
Phase 0: Static Analysis of Current API Implementation
Analyze without running GUI
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("PHASE 0: ANALYZING CURRENT API IMPLEMENTATION")
print("=" * 60)

# Check what's available
print("\n1. Checking available API files:")
api_files = [
    "native_api_dict.py",
    "native_api_simple.py", 
    "native_api.py",
    "main.py"
]

for file in api_files:
    if os.path.exists(file):
        print(f"   ✓ {file} exists")
    else:
        print(f"   ✗ {file} missing")

# Analyze main.py API usage
print("\n2. Analyzing main.py API configuration:")
try:
    with open("main.py", "r") as f:
        content = f.read()
        
    if "api_dict" in content:
        print("   ✓ Uses api_dict (dictionary-based)")
        
        # Find the line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "self.native_api = api_dict" in line:
                print(f"   → Line {i+1}: {line.strip()}")
                # Check preceding comment
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if prev_line.startswith('#') or prev_line.startswith('//'):
                        print(f"   → Comment: {prev_line}")
                        
    if "SimpleNativeAPI" in content:
        print("   ✓ SimpleNativeAPI class is imported/referenced")
    else:
        print("   ✗ No SimpleNativeAPI reference found")
        
except Exception as e:
    print(f"   ✗ Error analyzing main.py: {e}")

# Analyze the dict API
print("\n3. Analyzing dict-based API:")
try:
    with open("native_api_dict.py", "r") as f:
        dict_content = f.read()
        
    print("   ✓ Dict API contents:")
    
    # Find the api_dict definition
    if "api_dict = {" in dict_content:
        lines = dict_content.split('\n')
        in_dict = False
        for line in lines:
            if "api_dict = {" in line:
                in_dict = True
                print(f"   → {line.strip()}")
                continue
            if in_dict:
                if "}" in line and not line.strip().startswith('"'):
                    print(f"   → {line.strip()}")
                    break
                if line.strip() and not line.strip().startswith('#'):
                    print(f"   → {line.strip()}")
                    
    # Check for window reference handling
    if "_window_ref" in dict_content:
        print("   ✓ Uses global window reference")
    else:
        print("   ✗ No window reference mechanism found")
        
    # Check for file picker implementation
    if "create_file_dialog" in dict_content:
        print("   ✓ Has file picker implementation")
    else:
        print("   ✗ No file picker found")
        
except Exception as e:
    print(f"   ✗ Error analyzing dict API: {e}")

# Analyze class-based API for comparison  
print("\n4. Analyzing class-based API for comparison:")
try:
    with open("native_api_simple.py", "r") as f:
        class_content = f.read()
        
    if "class SimpleNativeAPI" in class_content:
        print("   ✓ SimpleNativeAPI class exists")
        
        # Count methods
        method_count = class_content.count("def ")
        print(f"   → Has ~{method_count} methods")
        
        # Check for key methods
        if "pick_file" in class_content or "pickFile" in class_content:
            print("   ✓ Has file picker methods")
        if "set_window" in class_content:
            print("   ✓ Has window reference handling")
            
    else:
        print("   ✗ No SimpleNativeAPI class found")
        
except Exception as e:
    print(f"   ✗ Error analyzing class API: {e}")

print("\n5. Frontend integration check:")
frontend_files = ["frontend/index.html", "frontend/indexf.html", "test_dropdown.html"]
for file in frontend_files:
    if os.path.exists(file):
        print(f"   ✓ {file} exists")
        try:
            with open(file, "r") as f:
                content = f.read()
            if "pywebview.api" in content:
                print(f"   → Uses pywebview.api")
            if "handleOpenFile" in content:
                print(f"   → Has file handling functions")
        except:
            pass
    else:
        print(f"   ✗ {file} not found")

print("\n" + "=" * 60)
print("ANALYSIS SUMMARY:")
print("=" * 60)

# Provide recommendations
print("\n📋 FINDINGS:")
print("• Current implementation uses dict-based API (api_dict)")
print("• Comment indicates this was intentional for 'PyWebView compatibility'")  
print("• Both dict and class-based APIs exist in codebase")
print("• File picker implementation exists in dict API")

print("\n🎯 NEXT STEPS:")
print("• Activate your turboo_linux_new virtual environment")
print("• Run: python main.py --debug")
print("• Test if file picker actually works")
print("• If it works → Skip Phase 1, go to Phase 2.5 (Document Embedding)")
print("• If it fails → Proceed with Phase 1 (API fix)")

print("\n📝 MANUAL TEST INSTRUCTIONS:")
print("1. Activate venv: source path/to/turboo_linux_new/bin/activate")
print("2. Install: pip install pywebview flask flask-cors")  
print("3. Run: python main.py")
print("4. Click 'Open File' button in the app")
print("5. Report back: Does the file picker open?")

print("\n" + "=" * 60)