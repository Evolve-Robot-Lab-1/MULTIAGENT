#!/usr/bin/env python3
"""Quick test to check what's working"""

import requests
import json
import sys

# Check if port is provided as argument
if len(sys.argv) > 1:
    PORT = sys.argv[1]
else:
    PORT = input("Enter the port number from the running application (check logs): ")

BASE_URL = f"http://localhost:{PORT}"

print(f"Testing DocAI Native endpoints on port {PORT}...")
print("-" * 50)

# Test health
try:
    resp = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"✓ Health check: {resp.status_code}")
    if resp.ok:
        print(f"  {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"✗ Health check failed: {e}")

print()

# Test config
try:
    resp = requests.get(f"{BASE_URL}/api/v1/config")
    print(f"✓ Config check: {resp.status_code}")
    if resp.ok:
        config = resp.json()
        print(f"  App: {config.get('app_name')} v{config.get('version')}")
        print(f"  LibreOffice: {config.get('libreoffice_available')}")
except Exception as e:
    print(f"✗ Config check failed: {e}")

print()

# Test HTML view
try:
    resp = requests.get(f"{BASE_URL}/view_document/test_document.txt")
    print(f"✓ HTML view test: {resp.status_code}")
    if resp.ok:
        result = resp.json()
        print(f"  Success: {result.get('success')}")
        print(f"  Type: {result.get('type')}")
except Exception as e:
    print(f"✗ HTML view failed: {e}")

print()

# Test native view (will likely fail without LibreOffice)
try:
    window_info = {"x": 100, "y": 100, "width": 1200, "height": 800}
    resp = requests.post(
        f"{BASE_URL}/api/v1/view_document_native/test_document.txt",
        json=window_info
    )
    print(f"✓ Native view test: {resp.status_code}")
    if resp.ok:
        result = resp.json()
        print(f"  Success: {result.get('success')}")
        if not result.get('success'):
            print(f"  Error: {result.get('error')}")
    else:
        print(f"  Error: {resp.text}")
except Exception as e:
    print(f"✗ Native view failed: {e}")

print("\n" + "-" * 50)
print("To access the UI, open your browser to:")
print(f"  {BASE_URL}/")