# DocAI_CLEAN_V1 Backup - 2025-06-19

This is a backup of the stable working version of DocAI with all integrated features.

## Git Information
- Commit: 3d2f6cd
- Tag: DocAI_CLEAN_V1_2025-06-19
- Date: June 19, 2025

## Features Included
- File upload with RAG processing
- Document viewing with LibreOffice UNO conversion
- Enhanced document viewer with full scrolling support
- Image embedding in documents
- Fixed dropdown menu onclick handlers
- Proper filename handling between frontend and backend
- Clean UI with left file panel, center viewer, right chat

## Files Backed Up
- enhanced-viewer.js - Enhanced document viewer functionality
- indexf.html - Main frontend HTML file
- app.js - Main application JavaScript
- stylenew.css - CSS styling
- main_copy.py - Backend Flask application
- rag_handler.py - RAG document processing
- libreoffice_uno_converter_improved.py - LibreOffice document conversion

## How to Restore
1. Copy all files from this backup directory to their original locations
2. Or use git: `git checkout DocAI_CLEAN_V1_2025-06-19`

## Running the Application
1. Start backend: `cd /path/to/docai_new_frontend && ./QUICK_START.sh`
2. Start frontend: `cd static2.0 && python3 -m http.server 8887`
3. Access at: http://localhost:8887/indexf.html