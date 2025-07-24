#!/usr/bin/env python3
"""
Minimal test to debug PyWebView API exposure issue
"""

import webview
import logging
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test 1: Simple dict API
def test_dict_api():
    logger.info("=== TEST 1: Dict API ===")
    
    def hello():
        logger.info("hello() called from JS")
        return "Hello from Python!"
    
    def get_time():
        logger.info("get_time() called from JS")
        return str(time.time())
    
    api = {
        "hello": hello,
        "get_time": get_time
    }
    
    logger.info(f"Dict API: {list(api.keys())}")
    
    window = webview.create_window(
        'Dict API Test',
        html='''
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Dict API Test</h1>
            <button onclick="testAPI()">Test API</button>
            <pre id="output"></pre>
            <script>
                function log(msg) {
                    document.getElementById('output').innerHTML += msg + '\\n';
                }
                
                async function testAPI() {
                    log('Testing dict API...');
                    log('typeof pywebview: ' + typeof pywebview);
                    log('typeof pywebview.api: ' + typeof pywebview.api);
                    
                    if (typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined') {
                        log('API keys: ' + Object.keys(pywebview.api).join(', '));
                        
                        try {
                            const result = await pywebview.api.hello();
                            log('hello() result: ' + result);
                        } catch (e) {
                            log('hello() error: ' + e.message);
                        }
                        
                        try {
                            const result = await pywebview.api.get_time();
                            log('get_time() result: ' + result);
                        } catch (e) {
                            log('get_time() error: ' + e.message);
                        }
                    }
                }
                
                // Test on load
                window.addEventListener('pywebviewready', testAPI);
                setTimeout(testAPI, 2000);
            </script>
        </body>
        </html>
        ''',
        js_api=api
    )
    
    webview.start(debug=True)

# Test 2: Class API
class TestAPI:
    def hello(self):
        logger.info("hello() called from JS (class)")
        return "Hello from class!"
    
    def get_time(self):
        logger.info("get_time() called from JS (class)")
        return str(time.time())

def test_class_api():
    logger.info("=== TEST 2: Class API ===")
    
    api = TestAPI()
    
    window = webview.create_window(
        'Class API Test',
        html='''
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Class API Test</h1>
            <button onclick="testAPI()">Test API</button>
            <pre id="output"></pre>
            <script>
                function log(msg) {
                    document.getElementById('output').innerHTML += msg + '\\n';
                }
                
                async function testAPI() {
                    log('Testing class API...');
                    log('typeof pywebview: ' + typeof pywebview);
                    log('typeof pywebview.api: ' + typeof pywebview.api);
                    
                    if (typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined') {
                        // Try to enumerate properties
                        try {
                            for (let key in pywebview.api) {
                                log('Found property: ' + key + ' (type: ' + typeof pywebview.api[key] + ')');
                            }
                        } catch (e) {
                            log('Error enumerating: ' + e.message);
                        }
                        
                        try {
                            const result = await pywebview.api.hello();
                            log('hello() result: ' + result);
                        } catch (e) {
                            log('hello() error: ' + e.message);
                        }
                    }
                }
                
                // Test on load
                window.addEventListener('pywebviewready', testAPI);
                setTimeout(testAPI, 2000);
            </script>
        </body>
        </html>
        ''',
        js_api=api
    )
    
    webview.start(debug=True)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'class':
        test_class_api()
    else:
        test_dict_api()