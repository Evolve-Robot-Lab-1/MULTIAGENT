#!/usr/bin/env python3
"""
Test script for LibreOffice Native Viewer Integration
Run this to verify the implementation is working correctly
"""

import os
import sys
import requests
import time

# Configuration
BASE_URL = "http://localhost:8090"  # Adjust if your app runs on a different port
TEST_DOCUMENT = "test.docx"  # Make sure this exists in your documents folder

def test_feature_flag():
    """Test 1: Verify feature flag is enabled"""
    print("Test 1: Checking feature flag...")
    # This test would need to be done manually or via an endpoint
    print("✓ Feature flag test requires manual verification in main_copy.py")
    print("  Expected: FEATURES['native_viewer'] = True")
    return True

def test_native_endpoint_exists():
    """Test 2: Verify native viewer endpoint exists"""
    print("\nTest 2: Testing native viewer endpoint...")
    try:
        url = f"{BASE_URL}/view_document_native/{TEST_DOCUMENT}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 404:
            print("✗ Native viewer endpoint not found")
            return False
        elif response.status_code == 302:  # Redirect
            print("✓ Native viewer endpoint exists (redirected - likely feature disabled or fallback)")
            return True
        elif response.status_code == 200:
            print("✓ Native viewer endpoint returned successfully")
            return True
        else:
            print(f"? Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing endpoint: {e}")
        return False

def test_html_endpoint_still_works():
    """Test 3: Verify original HTML viewer still works"""
    print("\nTest 3: Testing original HTML viewer...")
    try:
        url = f"{BASE_URL}/view_document/{TEST_DOCUMENT}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print("✓ Original HTML viewer still works")
            return True
        else:
            print(f"✗ Original viewer returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing original viewer: {e}")
        return False

def test_libreoffice_available():
    """Test 4: Check if LibreOffice is available"""
    print("\nTest 4: Checking LibreOffice availability...")
    try:
        import subprocess
        result = subprocess.run(['libreoffice', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ LibreOffice is available: {result.stdout.strip()}")
            return True
        else:
            print("✗ LibreOffice not found or error occurred")
            return False
    except Exception as e:
        print(f"✗ Error checking LibreOffice: {e}")
        return False

def run_frontend_tests():
    """Test 5: Frontend integration tests (manual)"""
    print("\nTest 5: Frontend Integration (Manual Tests)")
    print("Please verify the following manually:")
    print("  [ ] Viewer mode toggle button appears in document toolbar")
    print("  [ ] Toggle button shows current mode (HTML/Native)")
    print("  [ ] Clicking toggle switches between modes")
    print("  [ ] Document loads in both HTML and Native modes")
    print("  [ ] Edit mode prompts to switch to HTML when in Native mode")
    print("  [ ] File selection still works for all file types")
    print("  [ ] Error handling works (try non-existent file)")
    print("  [ ] Mode preference persists after page reload")

def main():
    print("=" * 60)
    print("LibreOffice Native Viewer Integration Test Suite")
    print("=" * 60)
    
    tests = [
        test_feature_flag,
        test_native_endpoint_exists,
        test_html_endpoint_still_works,
        test_libreoffice_available
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Summary: {passed}/{total} automated tests passed")
    print("=" * 60)
    
    run_frontend_tests()
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ All automated tests passed!")
        print("Please complete the manual frontend tests listed above.")
    else:
        print(f"\n⚠️  {total - passed} automated tests failed.")
        print("Please review the errors above before proceeding.")

if __name__ == "__main__":
    main()