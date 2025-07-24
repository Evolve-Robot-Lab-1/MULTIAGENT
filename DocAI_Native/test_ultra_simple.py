#!/usr/bin/env python3
"""
Ultra Simple Test - Minimal API to isolate the issue
"""

import webview
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Simple class with one method
class UltraSimpleAPI:
    def ping(self):
        """Test method"""
        logger.info("ping called!")
        return "pong"

def create_app():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ultra Simple Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                padding: 20px;
                text-align: center;
            }
            button {
                padding: 10px 20px;
                font-size: 16px;
                margin: 10px;
            }
            #result {
                margin-top: 20px;
                padding: 20px;
                background: #f0f0f0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>Ultra Simple API Test</h1>
        <button onclick="testPing()">Test Ping</button>
        <div id="result">Click button to test API</div>
        
        <script>
            console.log('Page loaded');
            
            window.addEventListener('pywebviewready', function() {
                console.log('PyWebView ready!');
                document.getElementById('result').innerHTML = 'PyWebView Ready - API should work now';
            });
            
            async function testPing() {
                console.log('Testing ping...');
                try {
                    if (!window.pywebview) {
                        throw new Error('pywebview not available');
                    }
                    if (!window.pywebview.api) {
                        throw new Error('pywebview.api not available');
                    }
                    
                    const result = await pywebview.api.ping();
                    console.log('Ping result:', result);
                    document.getElementById('result').innerHTML = 'SUCCESS: ' + result;
                } catch (e) {
                    console.error('Error:', e);
                    document.getElementById('result').innerHTML = 'ERROR: ' + e.message;
                }
            }
        </script>
    </body>
    </html>
    """
    
    # Create API
    api = UltraSimpleAPI()
    logger.info(f"API created: {api}")
    logger.info(f"API type: {type(api)}")
    logger.info(f"API ping method: {api.ping}")
    
    # Create window
    window = webview.create_window(
        'Ultra Simple Test',
        html=html,
        js_api=api
    )
    
    # Start
    webview.start(debug=True)

if __name__ == '__main__':
    print("Ultra Simple PyWebView Test")
    print("This is the simplest possible test case")
    print("-" * 40)
    create_app()