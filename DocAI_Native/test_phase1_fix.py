#!/usr/bin/env python3
"""
Test script to verify Phase 1 API fix
"""

import time
import sys

print("=" * 60)
print("PHASE 1 API FIX TEST")
print("=" * 60)
print()
print("This will test if the class-based API is working correctly.")
print()
print("1. Start the app: python main.py")
print("2. Look for these messages in the terminal:")
print("   - 'Creating SimpleNativeAPI instance for PyWebView'")
print("   - 'Native API type: <class 'native_api_simple.SimpleNativeAPI'>'")
print("   - '✓ checkLibreOffice method available'")
print("   - '✓ embedDocument method available'")
print()
print("3. In the app, click 'Test LibreOffice' button")
print("4. The file picker should open")
print("5. LibreOffice check should work")
print()
print("Starting app in 3 seconds...")
time.sleep(3)

# Run the main app
import subprocess
subprocess.run([sys.executable, "main.py"])