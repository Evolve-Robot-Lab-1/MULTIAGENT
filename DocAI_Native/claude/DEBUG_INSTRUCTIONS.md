# Debug Instructions for DocAI Native

## How to Enable Debug Mode

### Method 1: Environment Variable
```bash
export DOCAI_DEBUG=true
python main.py
```

### Method 2: Right-click in App
When the app is running, try:
- Right-click anywhere in the window
- Look for "Inspect Element" or "Developer Tools"
- This only works if debug mode is enabled

### Method 3: Keyboard Shortcuts
Try these while the app is running:
- F12 (Windows/Linux)
- Cmd+Option+I (macOS)
- Ctrl+Shift+I (Windows/Linux)

## Visual Debugging Added

Since console access is limited in PyWebView, I've added visual debugging:

1. **When you click "Open File"**, the center panel will show:
   - Confirmation that v1.7 is loaded
   - Whether PyWebView is detected
   - Whether the API is available
   - List of all available API methods

2. **What to look for**:
   - You should see "handleOpenFile v1.7 Called!" in the center
   - It should list methods like: pickFile, pickMultipleFiles, etc.
   - If no methods show, the API isn't being exposed properly

## To Test the Fix

1. **Restart the app completely**:
   ```bash
   python main.py
   ```

2. **Click "Files" → "Open File"**

3. **Look at the center panel** - it will show debug info

4. **Check Python console** for:
   - "SimpleNativeAPI initialized (v1.7 with camelCase methods)"
   - "pickFile called (camelCase wrapper)" when file picker should open

## If Still Not Working

The visual debug will tell us:
- If v1.7 is actually loaded (not cached v1.6)
- If PyWebView API is available
- What methods are exposed

This will help identify exactly where the problem is.