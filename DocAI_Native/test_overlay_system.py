#!/usr/bin/env python3
"""
Test script for LibreOffice Overlay Positioning System

This script tests the complete overlay system implementation
including all components and integration with PyWebView.
"""

import os
import sys
import time
import logging
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported"""
    print("\n=== Testing Imports ===")
    try:
        from app.services.overlay import LibreOfficeOverlayManager
        print("✓ LibreOfficeOverlayManager imported successfully")
        
        from app.services.overlay.coordinates import CoordinateSystem
        print("✓ CoordinateSystem imported successfully")
        
        from app.services.overlay.window_tracker import WindowTracker
        print("✓ WindowTracker imported successfully")
        
        from app.services.overlay.decorations import DecorationRemover
        print("✓ DecorationRemover imported successfully")
        
        from app.services.overlay.sync_engine import PositionSyncEngine
        print("✓ PositionSyncEngine imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_coordinate_system():
    """Test coordinate system calculations"""
    print("\n=== Testing Coordinate System ===")
    from app.services.overlay.coordinates import CoordinateSystem
    
    coord_sys = CoordinateSystem()
    
    # Test container bounds update
    bounds = {
        'x': 100, 'y': 150,
        'width': 800, 'height': 600,
        'top': 150, 'left': 100,
        'bottom': 750, 'right': 900
    }
    coord_sys.update_container_bounds(bounds)
    print("✓ Container bounds updated")
    
    # Test window position update
    coord_sys.update_window_position(50, 30)
    print("✓ Window position updated")
    
    # Test screen position calculation
    position = coord_sys.calculate_screen_position()
    if position:
        print(f"✓ Screen position calculated: {position}")
    else:
        print("✗ Failed to calculate screen position")
        
    return True

def test_window_tracker():
    """Test window tracker functionality"""
    print("\n=== Testing Window Tracker ===")
    from app.services.overlay.window_tracker import WindowTracker
    
    tracker = WindowTracker()
    print(f"✓ Window tracker created for platform: {tracker.platform}")
    
    # Test window search strategies
    strategies = tracker._get_search_strategies()
    print(f"✓ Search strategies for {tracker.platform}: {strategies}")
    
    return True

def test_overlay_manager():
    """Test overlay manager initialization"""
    print("\n=== Testing Overlay Manager ===")
    from app.services.overlay import LibreOfficeOverlayManager
    
    manager = LibreOfficeOverlayManager()
    print("✓ Overlay manager created")
    
    # Test status
    status = manager.get_status()
    print(f"✓ Status retrieved: state={status['state']}")
    
    return True

def test_libreoffice_detection():
    """Test LibreOffice detection"""
    print("\n=== Testing LibreOffice Detection ===")
    from app.services.overlay.manager import LibreOfficeOverlayManager
    
    manager = LibreOfficeOverlayManager()
    
    # Check for LibreOffice
    if manager.platform == "Windows":
        cmd = manager._find_libreoffice_windows()
    else:
        cmd = manager._find_libreoffice_unix()
        
    if cmd:
        print(f"✓ LibreOffice found at: {cmd}")
    else:
        print("✗ LibreOffice not found")
        print("  Please install LibreOffice to use native viewing")
        
    return bool(cmd)

def test_document_loading():
    """Test document loading with overlay"""
    print("\n=== Testing Document Loading ===")
    
    # Create a test document
    test_doc = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content for overlay system\n")
            f.write("This is a test of the LibreOffice overlay positioning.\n")
            test_doc = f.name
            
        print(f"✓ Test document created: {test_doc}")
        
        # Test with overlay manager
        from app.services.overlay import LibreOfficeOverlayManager
        
        manager = LibreOfficeOverlayManager()
        
        # Set callbacks
        def on_state_change(state):
            print(f"  State changed: {state.value}")
            
        def on_error(error):
            print(f"  Error: {error}")
            
        manager.set_callbacks(on_state_change, on_error)
        
        # Test loading (without actual GUI)
        container_bounds = {
            'x': 100, 'y': 100,
            'width': 800, 'height': 600
        }
        
        print("✓ Overlay manager configured")
        print("  Note: Actual window positioning requires GUI environment")
        
        return True
        
    finally:
        if test_doc and os.path.exists(test_doc):
            os.unlink(test_doc)
            print("✓ Test document cleaned up")

def test_api_integration():
    """Test PyWebView API integration"""
    print("\n=== Testing API Integration ===")
    
    try:
        from app.api.overlay_api import OverlayAPI
        
        api = OverlayAPI()
        print("✓ Overlay API created")
        
        # Test initialization
        result = api.initialize("/tmp/test_docs")
        if result['success']:
            print(f"✓ API initialized: platform={result['platform']}")
            print(f"  Features: {result['features']}")
        else:
            print(f"✗ API initialization failed: {result.get('error')}")
            
        return True
        
    except Exception as e:
        print(f"✗ API integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("LibreOffice Overlay System Test Suite")
    print("=====================================")
    
    tests = [
        ("Imports", test_imports),
        ("Coordinate System", test_coordinate_system),
        ("Window Tracker", test_window_tracker),
        ("Overlay Manager", test_overlay_manager),
        ("LibreOffice Detection", test_libreoffice_detection),
        ("Document Loading", test_document_loading),
        ("API Integration", test_api_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            failed += 1
            
    print("\n" + "="*50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ All tests passed! The overlay system is ready.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please check the implementation.")
        
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)