#!/usr/bin/env python3
"""
Minimal PyWebView dict API test
"""

import webview

# Simple dict API with basic functions
api = {
    "hello": lambda: "Hello from Python!",
    "add": lambda x, y: x + y,
    "get_list": lambda: ["apple", "banana", "orange"]
}

window = webview.create_window(
    'Simple Dict API Test',
    html='''
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Simple Dict API Test</h1>
        <button onclick="test()">Test API</button>
        <pre id="output"></pre>
        <script>
            async function test() {
                const output = document.getElementById('output');
                output.textContent = 'Testing...\n';
                
                try {
                    // Check if pywebview exists
                    output.textContent += 'pywebview exists: ' + (typeof pywebview !== 'undefined') + '\n';
                    output.textContent += 'pywebview.api exists: ' + (typeof pywebview?.api !== 'undefined') + '\n';
                    
                    if (pywebview && pywebview.api) {
                        // Test hello
                        const hello = await pywebview.api.hello();
                        output.textContent += 'hello(): ' + hello + '\n';
                        
                        // Test add
                        const sum = await pywebview.api.add(5, 3);
                        output.textContent += 'add(5, 3): ' + sum + '\n';
                        
                        // Test get_list
                        const list = await pywebview.api.get_list();
                        output.textContent += 'get_list(): ' + JSON.stringify(list) + '\n';
                    }
                } catch (e) {
                    output.textContent += 'Error: ' + e.message + '\n';
                }
            }
            
            // Auto-test after delay
            setTimeout(test, 1000);
        </script>
    </body>
    </html>
    ''',
    js_api=api
)

webview.start(debug=True)