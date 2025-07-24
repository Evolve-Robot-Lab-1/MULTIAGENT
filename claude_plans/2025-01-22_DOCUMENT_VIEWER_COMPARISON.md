# Document Viewer Comparison: Original DocAI vs DocAI_Native
**Date**: January 22, 2025
**Author**: Claude
**Status**: Analysis Complete

## 🎯 Executive Summary

The document viewing functionality in DocAI_Native is not working because of a fundamental architectural difference in how URLs are constructed and ports are handled. The original DocAI uses a fixed port (8090) with absolute URLs, while DocAI_Native uses dynamic ports with relative URLs, causing a mismatch in the request routing.

## 📊 Architecture Comparison

### Original DocAI (Working)

```
Architecture: Simple Flask Web App
Port: Fixed 8090
Frontend: static2.0/indexf.html
Backend: main_copy.py
URL Pattern: http://localhost:8090/view_document/filename
```

#### Key Implementation Details:
```javascript
// In indexf.html line 326
const response = await fetch(`http://localhost:8090/view_document/${encodeURIComponent(fileName)}`);
```

### DocAI_Native (Not Working)

```
Architecture: PyWebView Native App
Port: Dynamic (auto-assigned)
Frontend: frontend/index.html
Backend: backend_server.py
URL Pattern: /view_document/filename (relative)
```

#### Key Implementation Details:
```javascript
// In index.html line 866
const url = `/view_document/${encodeURIComponent(fileName)}`;
const response = await fetch(url);
```

## 🔍 Root Cause Analysis

### 1. **Port Configuration Difference**

**Original DocAI**:
- Uses hardcoded port 8090
- Frontend knows exactly where backend is
- Simple and predictable

**DocAI_Native**:
- Uses dynamic port (FLASK_PORT = 0 in config.py)
- Port assigned at runtime
- More flexible but requires proper URL handling

### 2. **URL Construction Issue**

The relative URL `/view_document/` only works when:
- Frontend is served from the same Flask server
- PyWebView correctly proxies requests
- The origin is properly set

Current issue: The relative URL might not be resolving to the correct backend endpoint.

### 3. **Missing Function Exports** (Fixed)

Previously missing exports:
- `displayDocumentFromBackend`
- `closeFileViewer`
- `enableEditMode`
- `displayFileInCenter`
- `askAboutSelection`
- `editSelection`

**Status**: ✅ Fixed by adding window exports

### 4. **Duplicate Function Definitions** (Fixed)

Two `addFileToContainer` functions existed:
- Lines 479-524 (first version)
- Lines 642-723 (second version with error handling)

**Status**: ✅ Fixed by removing first duplicate

### 5. **CSS Visibility Issues** (Fixed)

Missing styles for:
- `.word-viewer`
- `.file-viewer`

**Status**: ✅ Fixed by adding essential CSS

## 📈 Document Display Flow Comparison

### Original DocAI Flow:
```
1. User clicks file
2. handleFileClick() called
3. displayDocumentFromBackend() called
4. Fetch to http://localhost:8090/view_document/filename
5. Backend returns JSON with HTML in 'pages' array
6. HTML inserted into .chat-container
7. Document displays correctly
```

### DocAI_Native Flow (Current):
```
1. User clicks file ✓
2. handleFileClick() called ✓
3. displayDocumentFromBackend() called ✓
4. Fetch to /view_document/filename ✓
5. ❌ Request may not reach backend due to URL resolution
6. ❌ No response or error
7. ❌ Document doesn't display
```

## 🛠️ Fixes Applied So Far

1. **Function Exports** ✅
   - Added all missing window exports
   - Functions now globally accessible

2. **Duplicate Functions** ✅
   - Removed first addFileToContainer
   - Kept version with error handling

3. **CSS Styles** ✅
   - Added .word-viewer styles
   - Added .file-viewer styles

4. **Error Visibility** ✅
   - Enhanced error logging
   - Added debug panel output

5. **Refresh Button** ✅
   - Added event listener for refresh

## 🚨 Remaining Issues

### 1. **URL Resolution Problem** (CRITICAL)

The core issue is that the relative URL `/view_document/` may not be correctly resolved by PyWebView to the Flask backend running on a dynamic port.

**Symptoms**:
- Click handler fires correctly
- Functions are called
- Fetch request is made
- But document doesn't display

**Likely Cause**:
- PyWebView isn't routing the relative URL to the Flask backend
- Or the frontend isn't being served from the Flask server

### 2. **Frontend Serving Verification Needed**

Need to verify:
- Is Flask serving the frontend HTML?
- Is PyWebView loading from Flask or from file:///?
- What is window.location.origin in the PyWebView context?

## 💡 Solution Strategy

### Immediate Fix:
```javascript
// Use absolute URL with dynamic port discovery
const baseUrl = window.location.origin;
const response = await fetch(`${baseUrl}/view_document/${encodeURIComponent(fileName)}`);
```

### Debug Additions:
```javascript
console.log('[DEBUG] window.location:', window.location);
console.log('[DEBUG] origin:', window.location.origin);
console.log('[DEBUG] Full URL:', `${baseUrl}/view_document/${fileName}`);
```

### Backend Verification:
Ensure Flask is serving frontend:
```python
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')
```

## 📝 Next Steps

1. **Fix URL Construction**
   - Update fetch to use window.location.origin
   - Add fallback for file:// protocol

2. **Add PyWebView Debug**
   - Log all URL resolutions
   - Verify request routing

3. **Test Backend Directly**
   - Try accessing /view_document/ directly
   - Verify response format

4. **Consider Port Discovery**
   - If needed, implement port discovery mechanism
   - Store backend URL in global variable

## 🎯 Expected Outcome

Once the URL resolution is fixed, the document viewing should work as follows:
1. File click triggers proper backend fetch
2. LibreOffice converts DOCX to HTML
3. HTML displays in center panel
4. All features (edit, AI chat) become available

## 📚 References

- Original implementation: `/DocAI/static2.0/indexf.html`
- Current implementation: `/DocAI_Native/frontend/index.html`
- Backend routes: `/DocAI_Native/backend_server.py`
- Configuration: `/DocAI_Native/config.py`

---
**Note**: This comparison is based on code analysis as of January 22, 2025. The primary issue is the URL resolution between PyWebView and the Flask backend running on a dynamic port.