# Phase 1: Fix PyWebView API Registration - Native App Implementation Plan

## ⚠️ IMPORTANT UPDATE (2025-01-21)
**Critical Finding**: The current implementation already uses a dict-based API intentionally (see main.py line 214: "Using dict-based API for better PyWebView compatibility"). This Phase 1 plan may be based on outdated assumptions. **VERIFY FIRST** before implementing changes.

## 🎯 Phase 1 Objective
Fix the critical foundation issue where PyWebView cannot expose the native API to the webview. **NOTE**: First verify if the current dict-based approach is actually broken.

## 📍 Root Reference
This plan details Phase 1 from [UNIFIED_IMPLEMENTATION_PLAN.md](./UNIFIED_IMPLEMENTATION_PLAN.md#phase-1-fix-pywebview-api-registration-critical-foundation)

---

## 🔍 Understanding PyWebView Native App Architecture

### How PyWebView Works
```
Python Backend (main.py)
    ↓
Creates webview window with embedded browser engine
    ↓
Injects API object into JavaScript context
    ↓
Frontend (HTML/JS) runs inside webview
    ↓
JavaScript calls Python methods via pywebview.api
```

### The Current Problem
```
main.py passes dict → PyWebView expects class → API injection fails → JavaScript can't call Python
```

---

## 📋 Detailed Implementation Steps

### 🆕 Step 1.0: Verification Phase (DO THIS FIRST!)

**Purpose**: Confirm whether the current dict-based API is actually broken before making changes.

**Actions**:
1. **Test Current Implementation**
   ```bash
   cd DocAI_Native
   python main.py --debug
   ```
   
2. **Check for Functionality**
   - Does the app start without errors?
   - Can you access file dialogs from the UI?
   - Check terminal for API-related errors
   - Right-click → Inspect Element → Console for JavaScript errors

3. **Document Current State**
   ```python
   # Create test_current_api.py
   import webview
   from native_api_dict import api_dict
   
   window = webview.create_window(
       'Current API Test',
       html='<button onclick="testAPI()">Test API</button><div id="result"></div><script>async function testAPI() { try { const result = typeof pywebview !== "undefined" && typeof pywebview.api !== "undefined"; document.getElementById("result").innerText = "API Available: " + result + ", Methods: " + (result ? Object.keys(pywebview.api).join(", ") : "N/A"); } catch(e) { document.getElementById("result").innerText = "Error: " + e.message; } }</script>',
       js_api=api_dict,
       debug=True
   )
   webview.start()
   ```

4. **Decision Point**
   - ✅ If file dialogs work → Skip to Phase 2 (Document Embedding)
   - ❌ If API is broken → Continue with Step 1.1
   - ⚠️ If partially working → Document specific issues before proceeding

### Step 1.1: Understanding the Native App Structure

**Key Insight**: PyWebView creates a native window with an embedded web engine (not a browser). The "console" is accessed differently:

1. **Python Console**: Terminal where you run `python main.py`
2. **WebView DevTools**: Accessed via debug mode in PyWebView
3. **Log Files**: Where we'll write debug information

### Step 1.2: Enable PyWebView Debug Mode

**Location**: `main.py`, in `create_window` call

**Add debug parameter**:
```python
self.window = webview.create_window(
    title='Durga AI - Document Assistant',
    url=f'http://127.0.0.1:{port}',
    js_api=self.native_api,
    min_size=(1200, 800),
    debug=True  # ← ADD THIS: Opens DevTools in native window
)
```

**Note**: Debug mode adds a context menu (right-click) with "Inspect Element" option in the native window.

### Step 1.3: Fix the Import Statement

**Location**: `main.py`, imports section (top of file)

**Current**:
```python
from native_api_dict import api_dict
```

**Change to**:
```python
from native_api_simple import SimpleNativeAPI
```

### Step 1.4: Fix API Instantiation with Native Logging

**Location**: `main.py`, line 216 (in `__init__` method)

**Current**:
```python
self.native_api = api_dict
```

**Change to**:
```python
# Create instance of the API class
self.native_api = SimpleNativeAPI()

# Log to terminal (Python console)
logger.info("Created SimpleNativeAPI instance")
logger.info(f"API type: {type(self.native_api)}")
logger.info(f"API methods: {[m for m in dir(self.native_api) if not m.startswith('_')]}")

# Also create a debug file for verification
with open('api_debug.log', 'w') as f:
    f.write(f"API Setup Debug Log\n")
    f.write(f"==================\n")
    f.write(f"API Type: {type(self.native_api)}\n")
    f.write(f"Is SimpleNativeAPI: {isinstance(self.native_api, SimpleNativeAPI)}\n")
    f.write(f"Available Methods: {self.native_api.getAvailableMethods()}\n")
```

### Step 1.5: Set Window Reference for Native Dialogs

**Location**: `main.py`, after window creation

**Add after window creation**:
```python
# After: self.window = webview.create_window(...)
if hasattr(self.native_api, 'set_window'):
    self.native_api.set_window(self.window)
    logger.info("Window reference set - native file dialogs ready")
    
    # Test file dialog availability immediately
    logger.info("Testing native dialog availability...")
    try:
        # Don't actually open dialog, just check it's callable
        if hasattr(self.native_api, 'pick_file'):
            logger.info("✓ pick_file method exists")
        else:
            logger.error("✗ pick_file method NOT FOUND")
    except Exception as e:
        logger.error(f"Error checking file dialog: {e}")
```

### Step 1.6: Add Native App Verification

**Location**: `main.py`, add to App class

**Add Native Verification Method**:
```python
def verify_native_api(self):
    """Verify API is properly exposed to webview"""
    if not self.window:
        logger.error("Window not created yet")
        return False
    
    # Create verification HTML page
    verification_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Verification</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>Native API Verification</h1>
        <div id="results"></div>
        <button onclick="testPicker()">Test File Picker</button>
        
        <script>
            function addResult(label, success, detail) {
                const div = document.createElement('div');
                div.className = 'status ' + (success ? 'success' : 'error');
                div.innerHTML = `<strong>${label}:</strong> ${detail}`;
                document.getElementById('results').appendChild(div);
            }
            
            // Check PyWebView object
            addResult('PyWebView Object', 
                typeof pywebview !== 'undefined', 
                typeof pywebview !== 'undefined' ? 'Available' : 'NOT FOUND');
            
            // Check API object
            if (typeof pywebview !== 'undefined') {
                addResult('API Object', 
                    typeof pywebview.api !== 'undefined',
                    typeof pywebview.api !== 'undefined' ? 'Available' : 'NOT FOUND');
                
                // Check methods
                if (typeof pywebview.api !== 'undefined') {
                    addResult('pickFile Method',
                        typeof pywebview.api.pickFile === 'function',
                        typeof pywebview.api.pickFile === 'function' ? 'Callable' : 'NOT CALLABLE');
                    
                    // List all methods
                    try {
                        const methods = Object.getOwnPropertyNames(pywebview.api)
                            .filter(m => typeof pywebview.api[m] === 'function');
                        addResult('Available Methods', true, methods.join(', '));
                    } catch (e) {
                        addResult('Method Listing', false, e.message);
                    }
                }
            }
            
            async function testPicker() {
                try {
                    const result = await pywebview.api.pickFile();
                    addResult('File Picker Test', true, result || 'No file selected');
                } catch (e) {
                    addResult('File Picker Test', false, e.message);
                }
            }
        </script>
    </body>
    </html>
    """
    
    # Save verification page
    with open('verify_api.html', 'w') as f:
        f.write(verification_html)
    
    logger.info("Created verify_api.html - open in webview to test")
    
    # Also run automated test
    try:
        result = self.window.evaluate_js("""
            JSON.stringify({
                pywebview: typeof pywebview !== 'undefined',
                api: typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined',
                pickFile: typeof pywebview !== 'undefined' && 
                          typeof pywebview.api !== 'undefined' && 
                          typeof pywebview.api.pickFile === 'function'
            })
        """)
        
        import json
        status = json.loads(result)
        logger.info(f"Native API Status: {status}")
        
        with open('api_debug.log', 'a') as f:
            f.write(f"\nAPI Verification Results:\n")
            f.write(f"PyWebView available: {status['pywebview']}\n")
            f.write(f"API exposed: {status['api']}\n")
            f.write(f"pickFile callable: {status['pickFile']}\n")
        
        return status['pickFile']
        
    except Exception as e:
        logger.error(f"API verification failed: {e}")
        return False
```

### Step 1.7: Add Native Window Event Handlers

**Location**: `main.py`, in run method

**Add window event debugging**:
```python
def run(self):
    """Run the native application"""
    try:
        # Start Flask in background
        self.start_flask()
        
        # Configure window events for debugging
        def on_loaded():
            logger.info("Native window loaded")
            # Small delay for API injection
            import time
            time.sleep(0.5)
            
            # Verify API is available
            if self.debug_mode:
                self.verify_native_api()
        
        def on_shown():
            logger.info("Native window shown")
        
        # Set event handlers
        self.window.events.loaded += on_loaded
        self.window.events.shown += on_shown
        
        # Start the native window
        logger.info("Starting PyWebView native window...")
        webview.start(debug=self.debug_mode)
        
    except Exception as e:
        logger.error(f"Failed to start native app: {e}", exc_info=True)
```

### Step 1.8: Create Native Test Interface

**Create a test file**: `test_native_api.py`

```python
#!/usr/bin/env python3
"""
Direct test of native API without starting full app
"""
import sys
import logging
from native_api_simple import SimpleNativeAPI
import webview

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_native_api():
    """Test native API directly"""
    logger.info("Testing Native API...")
    
    # Create API instance
    api = SimpleNativeAPI()
    logger.info(f"API instance created: {type(api)}")
    
    # Check methods
    methods = api.getAvailableMethods()
    logger.info(f"Available methods: {methods}")
    
    # Create test window
    window = webview.create_window(
        'API Test',
        html='<h1>Check terminal for results</h1>',
        js_api=api,
        width=400,
        height=300
    )
    
    # Set window reference
    api.set_window(window)
    
    def test_in_window():
        # Test from Python side
        try:
            logger.info("Testing pick_file from Python...")
            result = api.pick_file()
            logger.info(f"Python result: {result}")
        except Exception as e:
            logger.error(f"Python test failed: {e}")
        
        # Test from JS side
        try:
            logger.info("Testing from JavaScript...")
            js_result = window.evaluate_js("""
                (async () => {
                    if (typeof pywebview === 'undefined') return 'pywebview not found';
                    if (typeof pywebview.api === 'undefined') return 'api not found';
                    if (typeof pywebview.api.pickFile !== 'function') return 'pickFile not a function';
                    return 'API looks good!';
                })()
            """)
            logger.info(f"JavaScript result: {js_result}")
        except Exception as e:
            logger.error(f"JavaScript test failed: {e}")
    
    window.events.loaded += test_in_window
    webview.start(debug=True)

if __name__ == '__main__':
    test_native_api()
```

---

## 🔧 Native App Troubleshooting

### Debugging in PyWebView (Not Browser!)

1. **Enable Debug Mode**:
   - Right-click in window → "Inspect Element"
   - This opens DevTools INSIDE the native window

2. **Check Python Terminal**:
   ```bash
   python main.py
   # Watch for:
   # INFO: Created SimpleNativeAPI instance
   # INFO: Window reference set - native file dialogs ready
   ```

3. **Check Debug Log**:
   ```bash
   cat api_debug.log
   # Should show API type and methods
   ```

4. **Run Test Script**:
   ```bash
   python test_native_api.py
   # Tests API without full app
   ```

### Native-Specific Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No debug menu on right-click | Debug mode not enabled | Add `debug=True` to create_window |
| File dialog doesn't appear | Window reference not set | Ensure `set_window()` is called |
| API undefined in webview | Wrong object type passed | Use class instance, not dict |
| Permission denied on file dialog | OS permissions | Check OS file dialog permissions |

---

## 🧪 Native App Verification

After implementing Phase 1:

- [ ] Terminal shows "Created SimpleNativeAPI instance"
- [ ] Terminal shows "Window reference set"
- [ ] `api_debug.log` exists and shows correct API type
- [ ] Right-click → Inspect works in native window
- [ ] DevTools console shows `pywebview.api` exists
- [ ] Test script `test_native_api.py` runs successfully
- [ ] File dialog opens when testing

---

## 🎯 Success Criteria for Native App

Phase 1 is complete when:

1. **Python Terminal** shows:
```
INFO: Created SimpleNativeAPI instance
INFO: API type: <class 'native_api_simple.SimpleNativeAPI'>
INFO: Window reference set - native file dialogs ready
INFO: Native window loaded
INFO: Native API Status: {'pywebview': True, 'api': True, 'pickFile': True}
```

2. **Native Window DevTools** (right-click → Inspect):
```javascript
> pywebview.api
SimpleNativeAPI {pickFile: ƒ, pickMultipleFiles: ƒ, ...}
> await pywebview.api.pickFile()
// Native file dialog appears
```

3. **Debug Log** (`api_debug.log`):
```
API Type: <class 'native_api_simple.SimpleNativeAPI'>
Is SimpleNativeAPI: True
Available Methods: ['pickFile', 'pick_file', ...]
```

---

## 📝 Key Differences: Native vs Browser

1. **No Browser Console** - Use PyWebView debug mode
2. **No F12** - Right-click → Inspect Element 
3. **No Network Tab** - Requests go through Python
4. **File Paths are Native** - Full OS paths, not web URLs
5. **Dialogs are OS Native** - Real file pickers, not web inputs

---

## 🚀 Next Steps

Once the native API is properly exposed (or verified working):
1. File picker can be called from JavaScript
2. Native OS dialog appears
3. File path is returned to JavaScript

Then proceed to:
- **If API was already working**: Skip to Phase 2.5 (Document Embedding Implementation)
- **If API was fixed**: Continue to Phase 2 (Frontend Integration)

## 🆕 Additional Improvements Needed

### Error Handling Enhancements
Based on codebase analysis, add these error handling improvements:

1. **Resource Limits**
   ```python
   # Add to native_api_simple.py
   MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
   
   def pick_file(self):
       filepath = self.window.create_file_dialog(webview.OPEN_DIALOG)
       if filepath and Path(filepath[0]).stat().st_size > MAX_FILE_SIZE:
           raise ValueError(f"File too large: {filepath[0]}")
       return filepath[0] if filepath else None
   ```

2. **Timeout Handling**
   ```python
   # Add to window operations
   import asyncio
   
   async def with_timeout(coro, timeout=30):
       try:
           return await asyncio.wait_for(coro, timeout=timeout)
       except asyncio.TimeoutError:
           logger.error(f"Operation timed out after {timeout}s")
           raise
   ```

3. **Platform-Specific Checks**
   ```python
   # Add platform validation
   if platform.system() not in ['Windows', 'Linux', 'Darwin']:
       logger.warning(f"Untested platform: {platform.system()}")
   ```

### Security Hardening
1. **Path Validation**: Ensure file paths don't escape allowed directories
2. **File Type Validation**: Check file extensions and MIME types
3. **Content Scanning**: Add hooks for malware scanning if required

### Missing Document Embedding Plan
**Critical Gap**: The plan focuses on API registration but doesn't address the actual LibreOffice embedding implementation. See Phase 2.5 in the updated unified plan for document embedding strategy.