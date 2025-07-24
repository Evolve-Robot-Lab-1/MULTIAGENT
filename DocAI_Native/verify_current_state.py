#!/usr/bin/env python3
"""
Phase 0: Verification Script
Test if the current dict-based API is working or broken
"""
import webview
import logging
import json
import sys
import os

# Add parent directory to path to import native_api_dict
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from native_api_dict import api_dict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_api():
    logger.info("=" * 50)
    logger.info("PHASE 0: TESTING CURRENT DICT-BASED API")
    logger.info("=" * 50)
    
    logger.info(f"Testing dict-based API: {type(api_dict)}")
    logger.info(f"Available methods: {list(api_dict.keys())}")
    
    # Create test window with comprehensive test UI
    window = webview.create_window(
        'API Verification - Phase 0',
        html='''<!DOCTYPE html>
<html>
<head>
    <title>API Verification</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 20px; 
            max-width: 800px; 
            margin: 0 auto;
        }
        h1 { color: #333; }
        .test-section {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .status {
            padding: 10px;
            margin: 5px 0;
            border-radius: 3px;
        }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .warning { background-color: #fff3cd; color: #856404; }
        button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 3px;
            background-color: #007bff;
            color: white;
            cursor: pointer;
        }
        button:hover { background-color: #0056b3; }
        #result { margin-top: 20px; }
        pre { background-color: #f5f5f5; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>DocAI Native - API Verification (Phase 0)</h1>
    
    <div class="test-section">
        <h2>1. Basic API Detection</h2>
        <button onclick="testBasicAPI()">Test Basic API</button>
        <div id="basic-result"></div>
    </div>
    
    <div class="test-section">
        <h2>2. Method Availability</h2>
        <button onclick="testMethods()">Test All Methods</button>
        <div id="methods-result"></div>
    </div>
    
    <div class="test-section">
        <h2>3. File Picker Test</h2>
        <button onclick="testFilePicker()">Test File Picker</button>
        <div id="picker-result"></div>
    </div>
    
    <div class="test-section">
        <h2>4. Full API Test</h2>
        <button onclick="runFullTest()">Run Full Test Suite</button>
        <div id="full-result"></div>
    </div>
    
    <script>
        function addResult(elementId, message, status = 'info') {
            const resultDiv = document.getElementById(elementId);
            const statusClass = status === 'success' ? 'success' : 
                               status === 'error' ? 'error' : 'warning';
            resultDiv.innerHTML = `<div class="status ${statusClass}">${message}</div>`;
        }
        
        function testBasicAPI() {
            try {
                const pywebviewExists = typeof pywebview !== 'undefined';
                const apiExists = pywebviewExists && typeof pywebview.api !== 'undefined';
                
                let message = `pywebview: ${pywebviewExists ? '✓ Found' : '✗ Not Found'}<br>`;
                message += `pywebview.api: ${apiExists ? '✓ Found' : '✗ Not Found'}`;
                
                if (apiExists) {
                    message += `<br>API Type: ${typeof pywebview.api}`;
                    message += `<br>API Constructor: ${pywebview.api.constructor.name}`;
                }
                
                addResult('basic-result', message, apiExists ? 'success' : 'error');
            } catch (e) {
                addResult('basic-result', 'Error: ' + e.message, 'error');
            }
        }
        
        function testMethods() {
            try {
                if (typeof pywebview === 'undefined' || typeof pywebview.api === 'undefined') {
                    addResult('methods-result', 'API not available', 'error');
                    return;
                }
                
                const methods = Object.keys(pywebview.api).filter(key => 
                    typeof pywebview.api[key] === 'function'
                );
                
                let message = `<strong>Found ${methods.length} methods:</strong><br>`;
                methods.forEach(method => {
                    message += `• ${method}<br>`;
                });
                
                // Test specific methods we expect
                const expectedMethods = ['pickFile', 'pick_file', 'getAvailableMethods'];
                const missing = expectedMethods.filter(m => !methods.includes(m));
                
                if (missing.length > 0) {
                    message += `<br><strong>Missing expected methods:</strong><br>`;
                    missing.forEach(m => message += `• ${m}<br>`);
                }
                
                addResult('methods-result', message, missing.length === 0 ? 'success' : 'warning');
            } catch (e) {
                addResult('methods-result', 'Error: ' + e.message, 'error');
            }
        }
        
        async function testFilePicker() {
            try {
                if (typeof pywebview === 'undefined' || typeof pywebview.api === 'undefined') {
                    addResult('picker-result', 'API not available', 'error');
                    return;
                }
                
                addResult('picker-result', 'Opening file picker...', 'warning');
                
                // Try different method names
                let result = null;
                let methodUsed = null;
                
                if (typeof pywebview.api.pickFile === 'function') {
                    result = await pywebview.api.pickFile();
                    methodUsed = 'pickFile';
                } else if (typeof pywebview.api.pick_file === 'function') {
                    result = await pywebview.api.pick_file();
                    methodUsed = 'pick_file';
                } else {
                    addResult('picker-result', 'No file picker method found!', 'error');
                    return;
                }
                
                if (result) {
                    addResult('picker-result', 
                        `✓ File picker worked!<br>Method: ${methodUsed}<br>Selected: ${result}`, 
                        'success'
                    );
                } else {
                    addResult('picker-result', 
                        `File picker opened but no file selected (this is OK)`, 
                        'warning'
                    );
                }
            } catch (e) {
                addResult('picker-result', 
                    `✗ File picker failed!<br>Error: ${e.message}`, 
                    'error'
                );
            }
        }
        
        async function runFullTest() {
            let results = {
                timestamp: new Date().toISOString(),
                pywebview: false,
                api: false,
                methods: [],
                pickFileWorks: false,
                errors: []
            };
            
            try {
                // Test 1: pywebview exists
                results.pywebview = typeof pywebview !== 'undefined';
                
                // Test 2: API exists
                results.api = results.pywebview && typeof pywebview.api !== 'undefined';
                
                if (results.api) {
                    // Test 3: Get methods
                    results.methods = Object.keys(pywebview.api).filter(key => 
                        typeof pywebview.api[key] === 'function'
                    );
                    
                    // Test 4: Try getAvailableMethods if it exists
                    if (typeof pywebview.api.getAvailableMethods === 'function') {
                        try {
                            const availableMethods = await pywebview.api.getAvailableMethods();
                            results.availableMethodsResponse = availableMethods;
                        } catch (e) {
                            results.errors.push('getAvailableMethods failed: ' + e.message);
                        }
                    }
                }
                
                // Generate report
                let report = '<h3>Full Test Report</h3><pre>' + JSON.stringify(results, null, 2) + '</pre>';
                
                // Summary
                const allGood = results.pywebview && results.api && results.methods.length > 0;
                report += `<h3>Summary</h3>`;
                report += `<div class="status ${allGood ? 'success' : 'error'}">`;
                report += allGood ? 
                    '✓ Dict-based API appears to be working!' : 
                    '✗ Dict-based API has issues';
                report += '</div>';
                
                addResult('full-result', report, allGood ? 'success' : 'error');
                
                // Log to console for Python side
                console.log('Full test results:', results);
                
            } catch (e) {
                results.errors.push('Full test error: ' + e.message);
                addResult('full-result', 
                    'Test suite error: ' + e.message + '<br><pre>' + JSON.stringify(results, null, 2) + '</pre>', 
                    'error'
                );
            }
        }
        
        // Run basic test on load
        window.addEventListener('load', () => {
            setTimeout(testBasicAPI, 500);
        });
    </script>
</body>
</html>''',
        js_api=api_dict,
        debug=True,
        width=900,
        height=700
    )
    
    def on_loaded():
        logger.info("Window loaded, API should be available")
        # Try to evaluate JavaScript to check API
        try:
            result = window.evaluate_js("""
                JSON.stringify({
                    pywebview: typeof pywebview !== 'undefined',
                    api: typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined',
                    apiType: typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined' ? 
                             typeof pywebview.api : 'N/A'
                })
            """)
            logger.info(f"JavaScript evaluation result: {result}")
        except Exception as e:
            logger.error(f"Failed to evaluate JavaScript: {e}")
        
    window.events.loaded += on_loaded
    
    logger.info("Starting PyWebView with dict-based API...")
    logger.info("Check the window for test results")
    logger.info("Press Ctrl+C to exit")
    
    webview.start()

if __name__ == '__main__':
    test_api()