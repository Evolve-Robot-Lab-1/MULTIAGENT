#!/usr/bin/env python3
"""
Quick test to run the main app and check if file picker works
"""
import subprocess
import sys
import time

print("=" * 60)
print("TESTING MAIN APP WITH CURRENT DICT-BASED API")
print("=" * 60)
print()
print("Starting DocAI Native app...")
print("Once the app opens:")
print("1. Click 'Open File' button")
print("2. Check if file picker opens")
print("3. Select a file and see if it loads")
print("4. Press Ctrl+C to stop")
print()
print("Starting in 3 seconds...")
time.sleep(3)

try:
    # Run the main app
    subprocess.run([sys.executable, "main.py", "--debug"], check=True)
except KeyboardInterrupt:
    print("\nApp stopped by user")
except Exception as e:
    print(f"\nError running app: {e}")