#!/usr/bin/env python3
"""
Direct test of PyWebView API to find working pattern
"""

import webview
import logging

logging.basicConfig(level=logging.DEBUG)

# Test 1: Direct instance methods
class API1:
    def test(self):
        return "API1 works!"

# Test 2: Init with methods
class API2:
    def __init__(self):
        self.test = lambda: "API2 works!"

# Test 3: Assigned methods
class API3:
    pass

api3 = API3()
api3.test = lambda: "API3 works!"

# Test 4: Direct object
api4 = type('API', (), {
    'test': lambda self: "API4 works!"
})()

def run_test(api_num):
    apis = {
        1: API1(),
        2: API2(),
        3: api3,
        4: api4
    }
    
    api = apis[api_num]
    print(f"Testing API pattern {api_num}")
    print(f"API type: {type(api)}")
    print(f"Has test method: {hasattr(api, 'test')}")
    
    window = webview.create_window(
        f'API Test {api_num}',
        html='''
        <html>
        <body>
            <h1>API Test</h1>
            <button onclick="test()">Test API</button>
            <pre id="output"></pre>
            <script>
                async function test() {
                    const output = document.getElementById('output');
                    output.textContent = 'Testing...\\n';
                    
                    if (typeof pywebview === 'undefined') {
                        output.textContent += 'pywebview is undefined\\n';
                        return;
                    }
                    
                    if (typeof pywebview.api === 'undefined') {
                        output.textContent += 'pywebview.api is undefined\\n';
                        return;
                    }
                    
                    output.textContent += 'API found!\\n';
                    output.textContent += 'API keys: ' + Object.keys(pywebview.api).join(', ') + '\\n';
                    
                    if (typeof pywebview.api.test === 'function') {
                        try {
                            const result = await pywebview.api.test();
                            output.textContent += 'Result: ' + result + '\\n';
                        } catch (e) {
                            output.textContent += 'Error: ' + e.message + '\\n';
                        }
                    } else {
                        output.textContent += 'test is not a function\\n';
                    }
                }
                
                setTimeout(test, 1000);
            </script>
        </body>
        </html>
        ''',
        js_api=api
    )
    
    webview.start(debug=True)

if __name__ == '__main__':
    import sys
    test_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_test(test_num)