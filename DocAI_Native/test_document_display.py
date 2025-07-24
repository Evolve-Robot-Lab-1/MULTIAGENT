#!/usr/bin/env python3
"""
Test script to verify document display functionality
"""

import requests
import json
import sys

def test_document_display():
    base_url = "http://localhost:8090"
    
    print("=== Testing Document Display in DocAI Native ===\n")
    
    # 1. Test files listing
    print("1. Testing /api/v1/files endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/files")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['count']} files")
            
            # Show first few files
            for i, file in enumerate(data['files'][:3]):
                print(f"   - {file['filename']} ({file['extension']})")
            
            if data['count'] > 3:
                print(f"   ... and {data['count'] - 3} more files")
                
            # Look for ERL-Offer_Letter.docx
            erl_file = next((f for f in data['files'] if 'ERL' in f['filename'] and f['extension'] == '.docx'), None)
            if erl_file:
                print(f"\n   ✅ Found ERL document: {erl_file['filename']}")
                return erl_file['filename']
            else:
                print("\n   ❌ ERL-Offer_Letter.docx not found in file list")
                return None
        else:
            print(f"   ❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_view_document(filename):
    base_url = "http://localhost:8090"
    
    print(f"\n2. Testing /view_document/{filename}...")
    try:
        response = requests.get(f"{base_url}/view_document/{filename}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"   ✅ Document loaded successfully")
                print(f"   - Pages: {data.get('total_pages', len(data.get('pages', [])))} ")
                print(f"   - Method: {data.get('method', 'N/A')}")
                print(f"   - Images: {data.get('images_found', 0)}")
                
                # Check content
                pages = data.get('pages', [])
                if pages and pages[0]:
                    print(f"   - Content length: {len(pages[0])} characters")
                    print(f"   - Has images: {'data:image' in pages[0]}")
                else:
                    print("   ⚠️  No content in pages")
                    
                return True
            else:
                print(f"   ❌ Failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ HTTP error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    # Test file listing
    filename = test_document_display()
    
    if filename:
        # Test document viewing
        success = test_view_document(filename)
        
        if success:
            print("\n✅ Document display functionality is working!")
            print("\nYou can now:")
            print("1. Click on 'ERL-Offer Letter.docx' in the DocAI Native app")
            print("2. The document should display in the center panel with images")
        else:
            print("\n❌ Document viewing failed")
    else:
        print("\n❌ Could not find document to test")
        
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()