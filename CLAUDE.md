# AI Assistant Instructions: LibreOffice Viewer Integration for Durga AI

## 🚨 CRITICAL: READ THIS FIRST

You are working on an **ENHANCEMENT** to an existing production system called "Durga AI". This is NOT a rewrite or replacement. ALL existing functionality MUST remain intact.

### Project Context
- **Application Name**: Durga AI (DocAI)
- **Current State**: Fully functional document viewer with AI chat integration
- **Your Task**: Add LibreOffice native viewer as an OPTIONAL viewing mode
- **Critical Constraint**: DO NOT break any existing functionality

## 🛡️ Code Preservation Rules

### RULE 1: Never Delete, Only Add
```
❌ NEVER DO THIS:
- Delete existing functions
- Remove existing routes
- Replace working code
- Modify core functionality

✅ ALWAYS DO THIS:
- Add new functions alongside existing ones
- Create new routes with different names
- Extend functionality with new options
- Use feature flags for new features
```

### RULE 2: Analyze Before Acting
Before making ANY changes:
1. Read the existing code thoroughly
2. Understand the current implementation
3. Identify integration points
4. Plan non-destructive additions

### RULE 3: Test Everything
After each change:
1. Verify existing features still work
2. Test file upload functionality
3. Confirm document viewing works
4. Check AI chat integration
5. Validate text selection features

## 📋 Implementation Phases

### Phase 1: Analysis (DO THIS FIRST)
```bash
# Required analysis tasks:
1. Read /static2.0/indexf.html - understand layout
2. Read /static2.0/app.js - understand document flow
3. Read /main_copy.py - understand backend routes
4. Read /app/services/libreoffice_uno_converter_improved.py
5. Document all findings before proceeding
```

### Phase 2: Backend Integration
```python
# In main_copy.py, ADD (don't replace) new route:
@app.route('/view_document_native/<filename>')
def view_document_native(filename):
    """
    NEW ROUTE for LibreOffice native viewer
    DO NOT modify existing view_document() route
    """
    # Implementation here
```

### Phase 3: Frontend Enhancement
```javascript
// In app.js or indexf.html, ADD new function:
function displayDocumentNative(filename) {
    // NEW function for native viewer
    // DO NOT modify displayDocumentFromBackend()
}

// Add viewer mode toggle:
let viewerMode = localStorage.getItem('viewerMode') || 'html';
```

### Phase 4: UI Integration
```html
<!-- Add toggle button to existing toolbar -->
<button id="viewer-mode-toggle" class="toolbar-btn">
    <span id="viewer-mode-text">HTML View</span>
</button>
```

## 🔍 Key Integration Points

### 1. Document Display Area
- **Current**: `.chat-container` div in middle panel
- **Integration**: Add iframe option within same container
- **Switching**: Toggle between HTML and iframe display

### 2. File Selection Flow
```javascript
// Current flow (DO NOT CHANGE):
handleFileClick() → displayDocumentFromBackend() → renders HTML

// New flow (ADD ALONGSIDE):
handleFileClick() → checkViewerMode() → 
  if (native) → displayDocumentNative()
  else → displayDocumentFromBackend()
```

### 3. Text Selection & AI Integration
- **Challenge**: Native LibreOffice viewer may not support JavaScript text selection
- **Solution**: Provide fallback to HTML view for AI features
- **Implementation**: Add notice when in native mode

## ⚠️ Common Pitfalls to Avoid

### 1. Breaking Existing Routes
```python
# ❌ WRONG:
@app.route('/view_document/<filename>')  # Don't modify this!
def view_document(filename):
    return libreoffice_native_view()  # This breaks existing functionality

# ✅ CORRECT:
@app.route('/view_document_native/<filename>')  # New route
def view_document_native(filename):
    return libreoffice_native_view()
```

### 2. Modifying Core Functions
```javascript
// ❌ WRONG:
function displayDocumentFromBackend(documentName) {
    // Completely new implementation
}

// ✅ CORRECT:
function displayDocumentFromBackend(documentName) {
    // Keep original implementation
}

function displayDocumentNative(documentName) {
    // New implementation here
}
```

### 3. Assuming LibreOffice is Installed
```python
# Always check and provide fallback:
try:
    import uno
    LIBREOFFICE_AVAILABLE = True
except ImportError:
    LIBREOFFICE_AVAILABLE = False
    
# In routes:
if not LIBREOFFICE_AVAILABLE:
    return redirect(url_for('view_document', filename=filename))
```

## 📊 Testing Checklist

After EACH change, verify:

### Existing Features:
- [ ] File upload works
- [ ] File list displays correctly
- [ ] Clicking file shows document
- [ ] AI chat responds to queries
- [ ] Text selection works (in HTML mode)
- [ ] Edit mode functions properly
- [ ] Context menu appears on selection
- [ ] "Ask about this" sends to chat
- [ ] Document metadata displays
- [ ] Zoom functionality works

### New Features:
- [ ] Viewer mode toggle appears
- [ ] Toggle switches between modes
- [ ] Native viewer loads documents
- [ ] Mode preference persists
- [ ] Fallback to HTML works
- [ ] Error handling functions

## 🚀 Implementation Order

1. **First**: Create feature flag system
2. **Second**: Add new backend route
3. **Third**: Implement frontend toggle
4. **Fourth**: Add native viewer display
5. **Fifth**: Implement mode switching
6. **Last**: Add error handling and fallbacks

## 💡 Best Practices

### 1. Use Feature Flags
```javascript
const FEATURES = {
    nativeViewer: true,  // Easy to disable if issues
    enhancedSelection: false
};
```

### 2. Maintain Backwards Compatibility
```python
def get_viewer_url(filename, mode='html'):
    if mode == 'native' and LIBREOFFICE_AVAILABLE:
        return url_for('view_document_native', filename=filename)
    return url_for('view_document', filename=filename)
```

### 3. Add Logging
```python
import logging
logger = logging.getLogger(__name__)

@app.route('/view_document_native/<filename>')
def view_document_native(filename):
    logger.info(f"Native viewer requested for: {filename}")
    # Implementation
```

## 🔄 Rollback Plan

If issues arise:
1. Set feature flag to false
2. Remove viewer mode toggle from UI
3. Default to HTML view
4. No data migration needed
5. No database changes to revert

## 📝 Documentation Requirements

For EVERY change:
1. Add inline comments explaining why
2. Document new functions/routes
3. Update this file with findings
4. Create examples of usage
5. Note any limitations discovered

## 🎯 Success Criteria

The integration is successful when:
1. ✅ All existing features work unchanged
2. ✅ Users can toggle between HTML and native view
3. ✅ Documents display correctly in both modes
4. ✅ No regression in current functionality
5. ✅ Errors handled gracefully with fallbacks

## 🆘 When to Stop and Ask

STOP and ask for guidance if:
- Any existing test fails
- Current functionality breaks
- Unsure about an integration point
- Need to modify core functions
- Database changes seem necessary

Remember: This is an ENHANCEMENT, not a replacement. When in doubt, preserve existing functionality over adding new features.