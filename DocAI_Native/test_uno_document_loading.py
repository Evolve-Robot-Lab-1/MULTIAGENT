#!/usr/bin/env python3
"""
Test script for UNO document loading functionality
Tests the enhanced uno_bridge.py implementation
"""

import sys
import logging
import time
from pathlib import Path
from uno_bridge import UNOSocketBridge, import_uno_modules

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_document():
    """Create a simple test document"""
    test_file = Path("test_document.txt")
    test_file.write_text("""
    Test Document for UNO Bridge
    ============================
    
    This is a test document to verify that:
    1. LibreOffice can be started via UNO
    2. Documents can be loaded
    3. Window handles can be extracted
    4. Document info can be retrieved
    
    If you can see this in LibreOffice, the integration is working!
    """)
    return str(test_file.absolute())

def test_uno_modules():
    """Test if UNO modules can be imported"""
    print("\n=== Testing UNO Module Import ===")
    if import_uno_modules():
        print("✅ UNO modules imported successfully")
        return True
    else:
        print("❌ Failed to import UNO modules")
        print("   Please install: sudo apt-get install python3-uno")
        return False

def test_libreoffice_startup(bridge):
    """Test LibreOffice server startup"""
    print("\n=== Testing LibreOffice Startup ===")
    if bridge.start_libreoffice_server():
        print(f"✅ LibreOffice started on port {bridge.port}")
        return True
    else:
        print("❌ Failed to start LibreOffice")
        return False

def test_document_loading(bridge, test_file):
    """Test document loading functionality"""
    print("\n=== Testing Document Loading ===")
    
    result = bridge.load_document(test_file)
    
    if result['success']:
        print(f"✅ Document loaded successfully")
        print(f"   Doc ID: {result['doc_id']}")
        print(f"   File: {result['file_path']}")
        
        if result.get('window'):
            window_info = result['window']
            print(f"   Window Type: {window_info['type']}")
            print(f"   Window Handle: {window_info['handle']}")
        else:
            print("   ⚠️  No window handle extracted")
            
        if result.get('info'):
            info = result['info']
            print(f"   Title: {info.get('title', 'N/A')}")
            print(f"   Pages: {info.get('pages', 'N/A')}")
        
        return True, result.get('doc_id')
    else:
        print(f"❌ Failed to load document: {result.get('error')}")
        return False, None

def test_document_info(bridge, doc_id):
    """Test getting document information"""
    print("\n=== Testing Document Info Retrieval ===")
    
    # Find the loaded document
    if doc_id in bridge.loaded_documents:
        doc = bridge.loaded_documents[doc_id]
        info = doc.get_document_info()
        
        print(f"✅ Document info retrieved:")
        print(f"   Doc ID: {info['doc_id']}")
        print(f"   Title: {info.get('title', 'N/A')}")
        print(f"   Author: {info.get('author', 'N/A')}")
        print(f"   Pages: {info.get('pages', 'N/A')}")
        print(f"   Created: {info.get('created', 'N/A')}")
        print(f"   Modified: {info.get('modified', 'N/A')}")
        return True
    else:
        print(f"❌ Document not found in loaded documents")
        return False

def test_embed_document(bridge, test_file):
    """Test the embed_document method"""
    print("\n=== Testing Document Embedding ===")
    
    result = bridge.embed_document(test_file, "test-container")
    
    if result.get('error'):
        print(f"❌ Embedding failed: {result['error']}")
        return False
    else:
        print(f"✅ Document embedding initiated")
        print(f"   Mode: {result.get('mode', 'N/A')}")
        print(f"   Container: {result.get('container', 'N/A')}")
        print(f"   Ready: {result.get('embedding_ready', False)}")
        print(f"   Message: {result.get('message', 'N/A')}")
        return True

def test_multiple_documents(bridge):
    """Test loading multiple documents"""
    print("\n=== Testing Multiple Document Loading ===")
    
    # Create additional test files
    test_files = []
    for i in range(3):
        test_file = Path(f"test_doc_{i}.txt")
        test_file.write_text(f"Test document {i}\nThis is document number {i}")
        test_files.append(str(test_file.absolute()))
    
    loaded_ids = []
    for file_path in test_files:
        result = bridge.load_document(file_path)
        if result['success']:
            loaded_ids.append(result['doc_id'])
            print(f"   ✅ Loaded: {Path(file_path).name} -> {result['doc_id']}")
        else:
            print(f"   ❌ Failed: {Path(file_path).name}")
    
    print(f"\nTotal loaded documents: {len(bridge.loaded_documents)}")
    
    # Clean up test files
    for file_path in test_files:
        Path(file_path).unlink(missing_ok=True)
    
    return len(loaded_ids) == len(test_files)

def test_bridge_status(bridge):
    """Test bridge status reporting"""
    print("\n=== Testing Bridge Status ===")
    
    status = bridge.get_status()
    print(f"✅ Bridge Status:")
    print(f"   Running: {status['running']}")
    print(f"   Port: {status['port']}")
    print(f"   Process Alive: {status['process_alive']}")
    print(f"   LibreOffice Path: {status['libreoffice_path']}")
    
    return status['running']

def main():
    """Run all tests"""
    print("=" * 60)
    print("UNO Document Loading Test Suite")
    print("=" * 60)
    
    # Check prerequisites
    if not test_uno_modules():
        print("\n❌ Cannot proceed without UNO modules")
        return 1
    
    # Create test document
    test_file = create_test_document()
    print(f"\nCreated test document: {test_file}")
    
    # Initialize bridge
    bridge = UNOSocketBridge()
    
    try:
        # Run tests
        tests_passed = 0
        total_tests = 0
        
        # Test 1: LibreOffice startup
        total_tests += 1
        if test_libreoffice_startup(bridge):
            tests_passed += 1
            time.sleep(2)  # Give LibreOffice time to fully start
        else:
            print("\n❌ Critical: Cannot start LibreOffice")
            return 1
        
        # Test 2: Document loading
        total_tests += 1
        success, doc_id = test_document_loading(bridge, test_file)
        if success:
            tests_passed += 1
            
            # Test 3: Document info
            total_tests += 1
            if test_document_info(bridge, doc_id):
                tests_passed += 1
        
        # Test 4: Document embedding
        total_tests += 1
        if test_embed_document(bridge, test_file):
            tests_passed += 1
        
        # Test 5: Multiple documents
        total_tests += 1
        if test_multiple_documents(bridge):
            tests_passed += 1
        
        # Test 6: Bridge status
        total_tests += 1
        if test_bridge_status(bridge):
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print(f"Test Summary: {tests_passed}/{total_tests} tests passed")
        print("=" * 60)
        
        if tests_passed == total_tests:
            print("\n✅ All tests passed! UNO document loading is working correctly.")
        else:
            print(f"\n⚠️  {total_tests - tests_passed} tests failed.")
        
        # Keep LibreOffice open for manual inspection
        if tests_passed > 0:
            print("\n📝 LibreOffice is still running. You can:")
            print("   - Check if the document is visible")
            print("   - Verify the window can be embedded")
            print("   - Press Enter to shutdown and exit")
            input()
        
    except Exception as e:
        logger.error(f"Test suite error: {e}", exc_info=True)
        return 1
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        bridge.shutdown()
        Path(test_file).unlink(missing_ok=True)
        print("✅ Cleanup complete")
    
    return 0 if tests_passed == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())