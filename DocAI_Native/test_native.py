#!/usr/bin/env python3
"""
Test script for DocAI Native
Verifies core functionality before building
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import webview
        print("✅ pywebview imported successfully")
    except ImportError as e:
        print(f"❌ pywebview import failed: {e}")
        return False
    
    try:
        import flask
        print("✅ flask imported successfully")
    except ImportError as e:
        print(f"❌ flask import failed: {e}")
        return False
    
    try:
        from config import CFG
        print(f"✅ config imported successfully - App: {CFG.APP_NAME}")
    except ImportError as e:
        print(f"❌ config import failed: {e}")
        return False
    
    try:
        from uno_bridge import UNOSocketBridge
        print("✅ uno_bridge imported successfully")
    except ImportError as e:
        print(f"❌ uno_bridge import failed: {e}")
        return False
    
    try:
        from native_api import NativeAPI
        print("✅ native_api imported successfully")
    except ImportError as e:
        print(f"❌ native_api import failed: {e}")
        return False
    
    try:
        from backend_server import create_app
        print("✅ backend_server imported successfully")
    except ImportError as e:
        print(f"❌ backend_server import failed: {e}")
        return False
    
    return True

def test_libreoffice():
    """Test LibreOffice availability"""
    print("\nTesting LibreOffice...")
    
    from config import CFG
    
    # Check if LibreOffice executable exists
    lo_path = Path(CFG.LIBREOFFICE_PATH)
    if lo_path.exists():
        print(f"✅ LibreOffice found at: {CFG.LIBREOFFICE_PATH}")
    else:
        print(f"⚠️  LibreOffice not found at: {CFG.LIBREOFFICE_PATH}")
        
        # Try alternatives
        alternatives = ["libreoffice", "soffice"]
        for alt in alternatives:
            try:
                result = subprocess.run([alt, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ LibreOffice found as: {alt}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        print("❌ LibreOffice not found in system")
        return False
    
    # Test UNO availability
    try:
        import uno
        print("✅ Python UNO module available")
        return True
    except ImportError:
        print("⚠️  Python UNO module not available")
        print("   Install with: sudo apt-get install python3-uno")
        return False

def test_uno_bridge():
    """Test UNO bridge functionality"""
    print("\nTesting UNO Bridge...")
    
    try:
        from uno_bridge import UNOSocketBridge
        bridge = UNOSocketBridge()
        
        print(f"✅ UNO Bridge created on port: {bridge.port}")
        
        # Test LibreOffice server start
        result = bridge.start_libreoffice_server()
        if result:
            print("✅ LibreOffice server started successfully")
            
            # Test status
            status = bridge.get_status()
            print(f"   Status: {status}")
            
            # Shutdown
            bridge.shutdown()
            print("✅ LibreOffice server shutdown successfully")
            return True
        else:
            print("❌ Failed to start LibreOffice server")
            return False
            
    except Exception as e:
        print(f"❌ UNO Bridge test failed: {e}")
        return False

def test_backend():
    """Test Flask backend creation"""
    print("\nTesting Backend...")
    
    try:
        from backend_server import create_app
        app = create_app()
        
        print(f"✅ Flask app created with {len(app.url_map._rules)} routes")
        
        # Test some basic routes
        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"⚠️  Health endpoint returned: {response.status_code}")
            
            response = client.get('/api/config')
            if response.status_code == 200:
                print("✅ Config endpoint working")
            else:
                print(f"⚠️  Config endpoint returned: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def test_frontend_files():
    """Test if frontend files exist"""
    print("\nTesting Frontend Files...")
    
    from config import CFG
    
    required_files = [
        CFG.FRONTEND_DIR / "index.html",
        CFG.FRONTEND_DIR / "static" / "css" / "stylenew.css",
        CFG.FRONTEND_DIR / "static" / "js" / "native-integration.js",
        CFG.FRONTEND_DIR / "static" / "assets" / "Durga.png"
    ]
    
    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"✅ {file_path.name} exists")
        else:
            print(f"❌ {file_path.name} missing")
            all_exist = False
    
    return all_exist

def test_document_processing():
    """Test document processing with a sample file"""
    print("\nTesting Document Processing...")
    
    try:
        # Create a test text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for DocAI Native.")
            test_file = f.name
        
        from backend_server import process_document_native
        result = process_document_native(test_file)
        
        if result.get('success'):
            print("✅ Document processing successful")
            print(f"   Type: {result.get('type')}")
            print(f"   Mode: {result.get('mode')}")
        else:
            print(f"❌ Document processing failed: {result.get('error')}")
            return False
        
        # Cleanup
        os.unlink(test_file)
        return True
        
    except Exception as e:
        print(f"❌ Document processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("DocAI Native - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("LibreOffice", test_libreoffice),
        ("UNO Bridge", test_uno_bridge),
        ("Backend", test_backend),
        ("Frontend Files", test_frontend_files),
        ("Document Processing", test_document_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to build and run.")
        print("Next steps:")
        print("  python main.py          # Run the application")
        print("  python build.py         # Build executable")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
        sys.exit(1)

if __name__ == '__main__':
    main()