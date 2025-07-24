# Native File Loading Fix

## Issues Fixed

### 1. Directory Search Mismatch
**Problem**: Files in `/home/erl/Documents/` were listed but returned 404 when clicked.
**Cause**: The `/api/v1/files` endpoint didn't include the parent Documents directory in its search paths, but `/view_document` did.
**Fix**: Added `CFG.DOCUMENTS_DIR.parent` to the search paths in `app/api/v1.py` line 569.

### 2. Port Configuration Mismatch
**Problem**: Frontend was hardcoded to use port 8090, but backend was using a random port.
**Cause**: `config.py` had `FLASK_PORT = 0` which means random port assignment.
**Fix**: Changed `FLASK_PORT = 8090` in `config.py` line 34.

## Changes Made

1. **app/api/v1.py** (line 569):
   - Added `CFG.DOCUMENTS_DIR.parent` to search_paths list
   - This ensures files in `/home/erl/Documents/` are included in file listing

2. **config.py** (line 34):
   - Changed `FLASK_PORT = 0` to `FLASK_PORT = 8090`
   - This ensures backend runs on the port expected by frontend

## How to Apply

1. Stop the current running instance of the app
2. Restart the app: `python3 main.py`
3. The app will now:
   - Run on port 8090 (matching frontend expectations)
   - List files from `/home/erl/Documents/`
   - Successfully load files when clicked

## Testing

1. Files in `/home/erl/Documents/` (like "ERL-Offer Letter.docx") should appear in the left panel
2. Clicking on these files should load them successfully without 404 errors
3. The app should be accessible at http://127.0.0.1:8090

## Note

The filename "ERL-Offer%20Letter.docx" is properly decoded to "ERL-Offer Letter.docx" in the UI thanks to the existing URL decoding logic.