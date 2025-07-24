# File Operations Tracker - DocAI Native

## Overview
This document tracks all file operation implementations found in the DocAI Native codebase. Each entry includes location, type, status, and recommendations for the native migration.

---

## 1. Frontend File Operations

### 1.1 index.html - Multiple handleOpenFile Implementations

#### A. Web-based File Picker (Lines 156-275)
```javascript
window.handleWebOpenFile = function() {
    const input = document.createElement('input');
    input.type = 'file';
    // Uses FileReader API
}
```
- **Type**: Web-based file input
- **Status**: ❌ BROKEN in PyWebView (FileReader.onload never fires)
- **Issues**: 
  - FileReader doesn't work in PyWebView environment
  - Relies on web APIs not available in native context
- **Recommendation**: 🗑️ **REMOVE** - Replace with native file picker

#### B. Router Function (Line 273)
```javascript
window.handleOpenFile = function() {
    window.handleWebOpenFile();
}
```
- **Type**: Router/wrapper function
- **Status**: ⚠️ Calls broken web function
- **Recommendation**: ✏️ **MODIFY** - Route to native picker instead

#### C. Unused Implementation (Line 518)
```javascript
window.handleOpenFile_real = handleOpenFileImpl;
```
- **Type**: Dead code
- **Status**: 💀 Unused/unreferenced
- **Recommendation**: 🗑️ **REMOVE** - Clean up dead code

### 1.2 native-integration.js - Native File Handlers

#### A. handleNativeOpenFile (Lines 147-184)
```javascript
async function handleNativeOpenFile() {
    const filePath = await NativeAPI.pickFile();
    // Adds to container and opens document
}
```
- **Type**: Native file picker integration
- **Status**: ✅ Properly implemented
- **Features**:
  - Uses PyWebView native API
  - Adds file to container
  - Shows success message
  - Opens document via backend
- **Recommendation**: ✅ **KEEP** - This is the correct implementation

#### B. handleNativeOpenMultiple (Lines 186-206)
```javascript
async function handleNativeOpenMultiple() {
    const filePaths = await NativeAPI.pickMultipleFiles();
    // Currently only opens first file
}
```
- **Type**: Multiple file selection
- **Status**: ⚠️ Partial implementation
- **Recommendation**: 🔄 **ENHANCE** - Complete multi-file support

#### C. handleOpenFolder (Lines 208-220)
```javascript
async function handleOpenFolder() {
    const folderPath = await NativeAPI.pickFolder();
    // TODO: Implement folder browsing
}
```
- **Type**: Folder selection
- **Status**: 🚧 Placeholder only
- **Recommendation**: 🔄 **ENHANCE** - Implement folder browsing

#### D. handleSaveAs (Lines 222-234)
```javascript
async function handleSaveAs() {
    const savePath = await NativeAPI.saveFile();
    // TODO: Implement save functionality
}
```
- **Type**: Save file dialog
- **Status**: 🚧 Placeholder only
- **Recommendation**: 🔄 **ENHANCE** - Implement save functionality

### 1.3 app.js - Additional File Operations

#### A. displayDocumentFromBackend (Line 518)
```javascript
window.displayDocumentFromBackend = function(documentName) {
    // Fetches and displays document HTML
}
```
- **Type**: Document display via backend
- **Status**: ✅ Working for HTML display
- **Recommendation**: ✅ **KEEP** - Needed for HTML view mode

#### B. uploadPDF Function
```javascript
window.uploadPDF = function() {
    // Web-based PDF upload
}
```
- **Type**: Web file upload
- **Status**: ❌ Uses FileReader (broken in PyWebView)
- **Recommendation**: ✏️ **MODIFY** - Use native file picker

---

## 2. Backend File Operations

### 2.1 Native API Implementations

#### A. native_api_simple.py - Class-based API
```python
class SimpleNativeAPI:
    def pick_file(self):  # Snake case
    def pickFile(self):   # Camel case wrapper
```
- **Type**: PyWebView API class
- **Status**: ✅ Correct implementation
- **Features**:
  - Both snake_case and camelCase methods
  - Proper window reference handling
  - Comprehensive error handling
- **Recommendation**: ✅ **KEEP** - This is the correct API

#### B. native_api_dict.py - Dictionary-based API
```python
api_dict = {
    "pickFile": pickFile,
    "pick_file": pick_file,
}
```
- **Type**: Dict-based API attempt
- **Status**: ❌ Doesn't work with PyWebView
- **Issues**: PyWebView requires class instance, not dict
- **Recommendation**: 🗑️ **REMOVE** - Use SimpleNativeAPI instead

### 2.2 main.py - API Registration

#### Current Implementation (Lines 214-252)
```python
self.native_api = api_dict  # ❌ WRONG
js_api=self.native_api
```
- **Type**: API registration
- **Status**: ❌ BROKEN - Using dict instead of class
- **Recommendation**: ✏️ **FIX IMMEDIATELY** - Use SimpleNativeAPI instance

### 2.3 backend_server.py - File Endpoints

#### A. /view_document_direct (Lines 96-178)
```python
@app.route('/view_document_direct', methods=['POST'])
def view_document_direct():
    # Handles native file paths
```
- **Type**: Native file path handler
- **Status**: ⚠️ Returns placeholder content
- **Recommendation**: ✏️ **MODIFY** - Implement proper document processing

#### B. /upload Endpoint
```python
@app.route('/upload', methods=['POST'])
def upload_file():
    # Web file upload handler
```
- **Type**: Web upload endpoint
- **Status**: ✅ Working for web mode
- **Recommendation**: ✅ **KEEP** - Fallback for web mode

---

## 3. Document Processing

### 3.1 document_processor.py
```python
class DocumentProcessor:
    def process_document(self, file_path):
```
- **Type**: Core document processing
- **Status**: ✅ Working
- **Features**: Text extraction, metadata, chunking
- **Recommendation**: ✅ **KEEP** - Core functionality

### 3.2 libreoffice_uno_converter_improved.py
```python
def convert_document_to_html(file_path):
```
- **Type**: LibreOffice conversion
- **Status**: ✅ Working
- **Recommendation**: ✅ **KEEP** - Needed for HTML view

---

## 4. UNO Bridge Integration

### 4.1 uno_bridge.py
```python
class UNOBridge:
    def load_document(self, filename, options):
```
- **Type**: LibreOffice UNO integration
- **Status**: ✅ Working
- **Features**: Document loading, conversion
- **Recommendation**: ✅ **KEEP** - Core for native viewing

### 4.2 window_manager.py
```python
class NativeWindowManager:
    def open_document_window(self, filename, parent_window_info):
```
- **Type**: Native window management
- **Status**: ✅ Implemented
- **Features**: X11 window positioning
- **Recommendation**: ✅ **KEEP** - Essential for embedding

---

## 5. Summary & Action Plan

### Immediate Actions Required:

1. **🔴 CRITICAL FIX**: In `main.py` line 216:
   ```python
   # CHANGE FROM:
   self.native_api = api_dict
   
   # TO:
   from native_api_simple import SimpleNativeAPI
   self.native_api = SimpleNativeAPI()
   self.native_api.set_window(self.window)
   ```

2. **🗑️ Remove These Files**:
   - `native_api_dict.py` - Doesn't work with PyWebView
   - Dead code in `index.html` (handleOpenFile_real)

3. **✏️ Modify These Functions**:
   - `handleOpenFile()` in index.html - Route to native picker
   - `uploadPDF()` - Use native file picker
   - `/view_document_direct` - Implement proper processing

4. **✅ Keep These Components**:
   - `native-integration.js` - Correct native implementation
   - `SimpleNativeAPI` class
   - `document_processor.py`
   - `uno_bridge.py`
   - `window_manager.py`

### File Selection Flow (Correct Path):
```
User clicks "Open File"
    ↓
handleOpenFile() [modify to check native mode]
    ↓
if (NativeAPI.isAvailable())
    → handleNativeOpenFile() [KEEP]
        → NativeAPI.pickFile() [KEEP]
        → openDocumentFromPath() [KEEP]
else
    → handleWebOpenFile() [web fallback]
```

### Key Issues to Fix:
1. **API Registration**: Use class instance, not dict
2. **handleOpenFile Router**: Check for native mode first
3. **Document Display**: Complete native viewer integration
4. **Multi-file Support**: Implement proper handling

This tracker provides a clear path for cleaning up the codebase while preserving working functionality.