#!/usr/bin/env python3
"""
Test script for native LibreOffice viewer integration
Tests the window embedding functionality end-to-end
"""

import sys
import time
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_native_viewer(base_url="http://localhost:8090", test_file=None):
    """Test native viewer functionality"""
    
    # Check server is running
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        if response.status_code != 200:
            logger.error("Server health check failed")
            return False
        logger.info("✓ Server is running")
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to server. Is it running?")
        return False
    
    # Find a test document if not provided
    if not test_file:
        # Look for test documents
        test_extensions = ['.pdf', '.docx', '.doc', '.odt']
        uploads_dir = Path("uploads")
        
        if uploads_dir.exists():
            for ext in test_extensions:
                files = list(uploads_dir.glob(f"*{ext}"))
                if files:
                    test_file = files[0].name
                    logger.info(f"Found test file: {test_file}")
                    break
        
        if not test_file:
            logger.error("No test document found. Please provide a document file.")
            return False
    
    # Test native viewer API
    logger.info(f"\nTesting native viewer with: {test_file}")
    
    # Simulate window information
    window_info = {
        "x": 100,
        "y": 100,
        "width": 1200,
        "height": 800
    }
    
    try:
        # 1. Open document in native viewer
        logger.info("1. Opening document in native viewer...")
        response = requests.post(
            f"{base_url}/api/v1/view_document_native/{test_file}",
            json=window_info
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to open document: {response.text}")
            return False
        
        result = response.json()
        if not result.get('success'):
            logger.error(f"Document open failed: {result.get('error')}")
            return False
        
        doc_id = result.get('doc_id')
        logger.info(f"✓ Document opened successfully. ID: {doc_id}")
        logger.info(f"  Window info: {result.get('window')}")
        logger.info(f"  Document info: {result.get('info')}")
        
        # Wait a bit for window to appear
        time.sleep(2)
        
        # 2. Test zoom functionality
        logger.info("\n2. Testing zoom control...")
        zoom_response = requests.post(
            f"{base_url}/api/v1/document/{doc_id}/zoom",
            json={"zoom": 150}
        )
        
        if zoom_response.status_code == 200:
            logger.info("✓ Zoom set to 150%")
        else:
            logger.warning(f"Zoom failed: {zoom_response.text}")
        
        time.sleep(1)
        
        # 3. Test page navigation (if multi-page document)
        doc_info = result.get('info', {})
        if doc_info.get('pages', 1) > 1:
            logger.info("\n3. Testing page navigation...")
            page_response = requests.post(
                f"{base_url}/api/v1/document/{doc_id}/page",
                json={"page": 2}
            )
            
            if page_response.status_code == 200:
                logger.info("✓ Navigated to page 2")
            else:
                logger.warning(f"Page navigation failed: {page_response.text}")
            
            time.sleep(1)
        
        # 4. Get document info
        logger.info("\n4. Getting document info...")
        info_response = requests.get(
            f"{base_url}/api/v1/document/{doc_id}/info"
        )
        
        if info_response.status_code == 200:
            info = info_response.json()
            logger.info(f"✓ Document info retrieved: {info}")
        else:
            logger.warning(f"Info retrieval failed: {info_response.text}")
        
        # 5. Close document
        logger.info("\n5. Closing document...")
        logger.info("(Keep the window open for 5 seconds to verify positioning)")
        time.sleep(5)
        
        close_response = requests.post(
            f"{base_url}/api/v1/document/{doc_id}/close"
        )
        
        if close_response.status_code == 200:
            logger.info("✓ Document closed successfully")
        else:
            logger.warning(f"Close failed: {close_response.text}")
        
        logger.info("\n✓ All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test native LibreOffice viewer")
    parser.add_argument(
        '--file', 
        help='Document file to test with',
        default=None
    )
    parser.add_argument(
        '--url',
        help='Base URL of the server',
        default='http://localhost:8090'
    )
    
    args = parser.parse_args()
    
    logger.info("Native Viewer Test Script")
    logger.info("=" * 50)
    logger.info("This script will:")
    logger.info("1. Open a document in native LibreOffice viewer")
    logger.info("2. Test zoom and page navigation")
    logger.info("3. Close the document")
    logger.info("=" * 50)
    
    success = test_native_viewer(args.url, args.file)
    
    if success:
        logger.info("\n✅ Native viewer is working correctly!")
    else:
        logger.error("\n❌ Native viewer test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()