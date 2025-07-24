#!/usr/bin/env python3
"""
Test script to document the functionality of the old DocAI system.
Run this before migration to capture baseline behavior.
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8090"
TEST_RESULTS = []

def log_result(test_name, endpoint, method, status_code, response_data, success=True):
    """Log test results."""
    result = {
        "timestamp": datetime.now().isoformat(),
        "test": test_name,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "success": success,
        "response": response_data
    }
    TEST_RESULTS.append(result)
    print(f"{'✅' if success else '❌'} {test_name}: {status_code}")
    return result

def test_health_check():
    """Test basic health check."""
    try:
        resp = requests.get(f"{BASE_URL}/")
        # Old system serves HTML, not JSON health
        log_result("Health Check", "/", "GET", resp.status_code, 
                  {"html_length": len(resp.text)}, resp.status_code == 200)
    except Exception as e:
        log_result("Health Check", "/", "GET", 0, {"error": str(e)}, False)

def test_rag_status():
    """Test RAG status endpoint."""
    try:
        resp = requests.get(f"{BASE_URL}/rag/status")
        data = resp.json()
        log_result("RAG Status", "/rag/status", "GET", resp.status_code, data)
        return data
    except Exception as e:
        log_result("RAG Status", "/rag/status", "GET", 0, {"error": str(e)}, False)
        return None

def test_chat_simple():
    """Test simple chat endpoint."""
    try:
        payload = {
            "prompt": "Hello, what is DocAI?",
            "session_id": "test-session-001"
        }
        resp = requests.post(f"{BASE_URL}/api/simple_chat", json=payload)
        data = resp.json()
        log_result("Simple Chat", "/api/simple_chat", "POST", resp.status_code, 
                  {"response_length": len(data.get("response", ""))})
    except Exception as e:
        log_result("Simple Chat", "/api/simple_chat", "POST", 0, {"error": str(e)}, False)

def test_chat_stream():
    """Test streaming chat endpoint."""
    try:
        payload = {
            "prompt": "List the documents you have access to",
            "session_id": "test-session-002",
            "use_rag": True
        }
        resp = requests.post(f"{BASE_URL}/api/query_stream", json=payload, stream=True)
        
        chunks = []
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    chunks.append(line_str[6:])
        
        log_result("Stream Chat", "/api/query_stream", "POST", resp.status_code,
                  {"chunks_received": len(chunks), "use_rag": True})
    except Exception as e:
        log_result("Stream Chat", "/api/query_stream", "POST", 0, {"error": str(e)}, False)

def test_agent_status():
    """Test agent status endpoint."""
    try:
        resp = requests.get(f"{BASE_URL}/api/agent-status")
        data = resp.json()
        log_result("Agent Status", "/api/agent-status", "GET", resp.status_code, data)
    except Exception as e:
        log_result("Agent Status", "/api/agent-status", "GET", 0, {"error": str(e)}, False)

def test_document_view():
    """Test document viewing."""
    try:
        # Try to view first document
        resp = requests.get(f"{BASE_URL}/view_document/SOURCES.txt")
        log_result("Document View", "/view_document/SOURCES.txt", "GET", 
                  resp.status_code, {"content_length": len(resp.text)}, 
                  resp.status_code == 200)
    except Exception as e:
        log_result("Document View", "/view_document/SOURCES.txt", "GET", 0, 
                  {"error": str(e)}, False)

def test_clear_chat():
    """Test clearing chat history."""
    try:
        payload = {"session_id": "test-session-001"}
        resp = requests.post(f"{BASE_URL}/api/clear_chat", json=payload)
        data = resp.json()
        log_result("Clear Chat", "/api/clear_chat", "POST", resp.status_code, data)
    except Exception as e:
        log_result("Clear Chat", "/api/clear_chat", "POST", 0, {"error": str(e)}, False)

def save_results():
    """Save test results to file."""
    results = {
        "test_run": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "total_tests": len(TEST_RESULTS),
        "passed": sum(1 for r in TEST_RESULTS if r["success"]),
        "failed": sum(1 for r in TEST_RESULTS if not r["success"]),
        "results": TEST_RESULTS
    }
    
    with open("old_system_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Test Summary:")
    print(f"Total: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"\nResults saved to: old_system_test_results.json")

def main():
    """Run all tests."""
    print("🧪 Testing Old DocAI System")
    print("=" * 50)
    
    # Check if system is running
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("❌ Old system not running on port 8090!")
        print("Start it with: python3 main_copy.py")
        return
    
    # Run tests
    test_health_check()
    rag_data = test_rag_status()
    test_chat_simple()
    test_chat_stream()
    test_agent_status()
    test_document_view()
    test_clear_chat()
    
    # Save results
    save_results()
    
    # Print document info
    if rag_data:
        print(f"\n📄 Documents in system: {rag_data['document_count']}")
        for doc in rag_data.get('documents', []):
            print(f"  - {doc}")

if __name__ == "__main__":
    main()