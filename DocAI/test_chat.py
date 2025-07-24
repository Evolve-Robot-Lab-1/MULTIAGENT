#!/usr/bin/env python3
"""Test script to verify chat functionality"""

import requests
import json
import sys

# Base URL for the API
BASE_URL = "http://127.0.0.1:8090"

def test_health():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_simple_chat():
    """Test simple chat endpoint"""
    try:
        payload = {
            "message": "Hello, can you tell me what you can help with?",
            "language": "en"
        }
        response = requests.post(f"{BASE_URL}/api/simple_chat", json=payload)
        print(f"\nSimple chat: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Simple chat failed: {e}")
        return False

def test_streaming_chat():
    """Test streaming chat endpoint"""
    try:
        payload = {
            "query": "What is the weather like today?",
            "language": "en"
        }
        response = requests.post(f"{BASE_URL}/api/query_stream", json=payload, stream=True)
        print(f"\nStreaming chat: {response.status_code}")
        print("Streaming response:")
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    data = decoded_line[6:]
                    if data == 'END_OF_STREAM':
                        print("Stream ended")
                        break
                    try:
                        parsed = json.loads(data)
                        if 'text' in parsed:
                            print(parsed['text'], end='', flush=True)
                    except:
                        print(f"Raw data: {data}")
        print("\n")
        return response.status_code == 200
    except Exception as e:
        print(f"Streaming chat failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing DocAI Chat Integration")
    print("=" * 40)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Simple Chat", test_simple_chat),
        ("Streaming Chat", test_streaming_chat)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    # Exit with appropriate code
    sys.exit(0 if all(r[1] for r in results) else 1)