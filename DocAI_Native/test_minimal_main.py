#!/usr/bin/env python3
"""
Minimal test of PyWebView with basic API
"""

import webview
import logging

logging.basicConfig(level=logging.DEBUG)

# Import minimal API
from native_api_minimal import minimal_api

# Create window with minimal API
window = webview.create_window(
    'Minimal API Test',
    url='http://127.0.0.1:5000/test_pywebview_api.html',
    js_api=minimal_api
)

print("Starting PyWebView with minimal API...")
print(f"API type: {type(minimal_api)}")
print(f"API methods: {list(minimal_api.keys())}")

webview.start(debug=True)