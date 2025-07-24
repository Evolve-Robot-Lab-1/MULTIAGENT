#!/usr/bin/env python3
"""
Test PyWebView API access patterns
"""

import webview
import time

# Test different API patterns
def test_pattern_1():
    """Pattern 1: Direct function references"""
    print("Testing Pattern 1: Direct function references")
    
    def hello():
        return "Hello from Pattern 1"
    
    def get_time():
        return str(time.time())
    
    api = {
        "hello": hello,
        "get_time": get_time
    }
    
    return api

def test_pattern_2():
    """Pattern 2: Lambda functions"""
    print("Testing Pattern 2: Lambda functions")
    
    api = {
        "hello": lambda: "Hello from Pattern 2",
        "get_time": lambda: str(time.time())
    }
    
    return api

def test_pattern_3():
    """Pattern 3: Class instance"""
    print("Testing Pattern 3: Class instance")
    
    class API:
        def hello(self):
            return "Hello from Pattern 3"
        
        def get_time(self):
            return str(time.time())
    
    return API()

def test_pattern_4():
    """Pattern 4: Object with __getitem__"""
    print("Testing Pattern 4: Object with __getitem__")
    
    class APIDict:
        def __init__(self):
            self._methods = {
                "hello": lambda: "Hello from Pattern 4",
                "get_time": lambda: str(time.time())
            }
        
        def __getitem__(self, key):
            return self._methods[key]
        
        def __contains__(self, key):
            return key in self._methods
        
        def keys(self):
            return self._methods.keys()
    
    return APIDict()

# HTML template for testing
html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>API Pattern Test</title>
    <style>
        body {{ font-family: monospace; padding: 20px; }}
        .log {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>Testing Pattern: {pattern_name}</h1>
    <div class="log" id="log">Waiting for API...</div>
    
    <script>
        const log = document.getElementById('log');
        
        function addLog(msg) {{
            log.innerHTML += '<br>' + new Date().toISOString() + ': ' + msg;
        }}
        
        async function testAPI() {{
            addLog('Starting API test...');
            
            // Check pywebview
            if (typeof pywebview === 'undefined') {{
                addLog('ERROR: pywebview is undefined');
                return;
            }}
            addLog('✓ pywebview exists');
            
            // Check api
            if (typeof pywebview.api === 'undefined') {{
                addLog('ERROR: pywebview.api is undefined');
                return;
            }}
            addLog('✓ pywebview.api exists');
            
            // Check type
            addLog('API type: ' + typeof pywebview.api);
            addLog('API constructor: ' + pywebview.api.constructor.name);
            
            // Try to list properties
            try {{
                const keys = Object.keys(pywebview.api);
                addLog('API keys: ' + keys.join(', '));
            }} catch (e) {{
                addLog('Cannot get keys: ' + e.message);
            }}
            
            // Test hello method
            try {{
                if (typeof pywebview.api.hello === 'function') {{
                    const result = await pywebview.api.hello();
                    addLog('✓ hello() returned: ' + result);
                }} else {{
                    addLog('ERROR: hello is not a function');
                }}
            }} catch (e) {{
                addLog('ERROR calling hello: ' + e.message);
            }}
            
            // Test get_time method
            try {{
                if (typeof pywebview.api.get_time === 'function') {{
                    const result = await pywebview.api.get_time();
                    addLog('✓ get_time() returned: ' + result);
                }} else {{
                    addLog('ERROR: get_time is not a function');
                }}
            }} catch (e) {{
                addLog('ERROR calling get_time: ' + e.message);
            }}
        }}
        
        // Test on various events
        window.addEventListener('DOMContentLoaded', () => {{
            addLog('DOM loaded');
            setTimeout(testAPI, 1000);
        }});
        
        window.addEventListener('pywebviewready', () => {{
            addLog('pywebviewready event!');
            testAPI();
        }});
        
        // Also check periodically
        let checkCount = 0;
        const interval = setInterval(() => {{
            checkCount++;
            if (typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined') {{
                addLog('API detected after ' + checkCount + ' checks');
                clearInterval(interval);
                testAPI();
            }} else if (checkCount > 20) {{
                addLog('API not found after 20 checks');
                clearInterval(interval);
            }}
        }}, 100);
    </script>
</body>
</html>
'''

def run_test(pattern_num):
    """Run test for a specific pattern"""
    patterns = {
        1: test_pattern_1,
        2: test_pattern_2,
        3: test_pattern_3,
        4: test_pattern_4
    }
    
    if pattern_num not in patterns:
        print(f"Invalid pattern number: {pattern_num}")
        return
    
    pattern_func = patterns[pattern_num]
    api = pattern_func()
    
    window = webview.create_window(
        f'API Pattern {pattern_num} Test',
        html=html_template.format(pattern_name=f"Pattern {pattern_num}"),
        js_api=api
    )
    
    webview.start(debug=True)

if __name__ == '__main__':
    import sys
    pattern = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_test(pattern)