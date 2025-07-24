# Native App Restart Guide

## Changes Made for Native App

### 1. Cache Clearing on Startup
- Added automatic PyWebView cache clearing in `main.py`
- Clears caches from multiple locations before window creation
- This ensures CSS/JS changes are loaded fresh each time

### 2. Fixed File Handlers
- **Open File**: Now correctly uses `handleOpenFile()` which detects native mode
- **Direct File Viewing**: Added `/view_document_direct` endpoint for native file paths
- Files selected via native picker will now display properly

### 3. Auto-load Files on Startup
- Files now automatically load in the left container when app starts
- No need to click refresh button first

## How to Apply Changes

### Step 1: Stop Current Instance
```bash
# Press Ctrl+C in the terminal where DocAI_Native is running
```

### Step 2: Restart the Application
```bash
cd /media/erl/New\ Volume/ai_agent/BROWSER\ AGENT/docai_final/DocAI_Native
python main.py
```

### What Happens on Restart:
1. **Cache Clearing**: PyWebView caches will be automatically cleared
2. **Fresh Load**: All CSS and JavaScript changes will be loaded
3. **Console Output**: You'll see "Cleared cache at: [path]" messages

## Expected Behavior After Restart

1. **Dropdown Menus**: Click Files/Agents/Language - dropdowns should appear
2. **Open File**: 
   - Click Files → Open File
   - Native file picker dialog appears
   - Select a file → it displays in center panel
3. **File List**: Files automatically load in left container on startup
4. **File Viewing**: Click any file in left panel → content displays in center

## Troubleshooting

If issues persist after restart:

1. **Check Console Output**:
   - Look for "Cleared cache at:" messages
   - Check for any error messages during startup

2. **Verify File Permissions**:
   ```bash
   ls -la frontend/static/css/
   ls -la frontend/static/js/
   ```

3. **Manual Cache Clear** (if needed):
   ```bash
   # Linux
   rm -rf ~/.cache/pywebview
   rm -rf ~/.pywebview
   
   # Windows
   rmdir /s %LOCALAPPDATA%\pywebview
   
   # macOS
   rm -rf ~/Library/Caches/pywebview
   ```

## Native Mode Features

In native mode:
- **File Picker**: Uses system file dialog
- **Direct File Access**: Can open files from anywhere on system
- **No Upload Needed**: Files are accessed directly from their location

## Summary

The main fixes:
1. ✅ PyWebView cache clearing on startup
2. ✅ Fixed "Open File" to work in native mode
3. ✅ Direct file viewing for native-selected files
4. ✅ Auto-load files on startup

Just restart the application and all changes will take effect!