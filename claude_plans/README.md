# DocAI Native - Desktop Application

A native desktop version of Durga AI with embedded LibreOffice document viewing capabilities.

## Features

- 🖥️ **Native Desktop App** - No browser required
- 📄 **LibreOffice Integration** - Native document viewing with UNO socket bridge
- 🚀 **Fast Performance** - Direct file access, no network overhead
- 🔧 **Modular Architecture** - Easy to extend and maintain
- 🎯 **Same Functionality** - All features from web version preserved

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **LibreOffice** (with UNO support)
3. **System Dependencies**:
   - Linux: `sudo apt-get install python3-uno libreoffice`
   - Windows: Install LibreOffice from official website
   - macOS: `brew install libreoffice`

### Installation

```bash
# Clone and navigate
cd DocAI_Native

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Building Executable

```bash
# Build single executable
python build.py

# Run the executable
./dist/DurgaAI-Native
```

## Architecture

```
┌─────────────────────────────────────────────┐
│               DocAI Native                  │
├─────────────────────────────────────────────┤
│  PyWebView Window (Native GUI)             │
│  ├─ HTML/CSS/JS Frontend                   │
│  ├─ Flask Backend (Embedded)               │
│  └─ Native API Bridge                      │
├─────────────────────────────────────────────┤
│  LibreOffice UNO Bridge                    │
│  ├─ Socket Communication                   │
│  ├─ Document Embedding (Prototype)         │
│  └─ Future: LibreOfficeKit Integration     │
└─────────────────────────────────────────────┘
```

## Key Components

### Backend (`backend_server.py`)
- Modified Flask app for native use
- Direct file system access (no uploads)
- Reuses existing DocAI processing logic

### Native API (`native_api.py`)
- Bridge between JavaScript and Python
- File picker dialogs
- System integration
- LibreOffice control

### UNO Bridge (`uno_bridge.py`)
- LibreOffice socket communication
- Document embedding (prototype)
- Graceful error handling

### Frontend (`frontend/`)
- Modified HTML/CSS/JS from web version
- Native integration hooks
- Enhanced file operations

## Usage

### Opening Documents
1. **File Menu → Open File** - Native file picker
2. **Drag & Drop** - Drop files onto window (coming soon)
3. **Command Line** - `python main.py --open document.docx`

### LibreOffice Integration
- Automatically starts LibreOffice UNO server
- Embeds documents in native viewer
- Falls back to HTML view if needed

### Development Mode
```bash
# Enable debug mode
python main.py --debug

# Specify custom port
python main.py --port 5001
```

## Configuration

Edit `config.py` to customize:

```python
# Window settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# LibreOffice path
LIBREOFFICE_PATH = "/usr/bin/libreoffice"

# Enable debug mode
DEBUG = True
```

## Roadmap

### Current (v0.1.0)
- ✅ PyWebView wrapper
- ✅ Native file operations
- ✅ UNO socket bridge (prototype)
- ✅ Basic document viewing

### Next Sprint (v0.2.0)
- 🔄 LibreOfficeKit integration
- 🔄 True document embedding
- 🔄 Improved error handling
- 🔄 Auto-update system

### Future (v1.0.0)
- 📋 Full native widgets (PyQt6)
- 📋 Multi-document interface
- 📋 Advanced collaboration
- 📋 Plugin system

## Development

### Project Structure
```
DocAI_Native/
├── main.py              # Entry point
├── config.py            # Configuration
├── backend_server.py    # Flask backend
├── native_api.py        # Native API bridge
├── uno_bridge.py        # LibreOffice integration
├── requirements.txt     # Dependencies
├── build.py            # Build script
└── frontend/           # Web frontend
    ├── index.html
    └── static/
        ├── css/
        ├── js/
        └── assets/
```

### Adding Features

1. **Backend**: Add routes to `backend_server.py`
2. **Frontend**: Modify files in `frontend/`
3. **Native**: Extend `native_api.py` for system integration
4. **LibreOffice**: Enhance `uno_bridge.py` for document features

### Testing

```bash
# Run with debug mode
python main.py --debug

# Test specific file
python main.py --open test.docx

# Check LibreOffice integration
python -c "from uno_bridge import UNOSocketBridge; bridge = UNOSocketBridge(); print(bridge.start_libreoffice_server())"
```

## Troubleshooting

### LibreOffice Issues
- **"LibreOffice not found"**: Check `LIBREOFFICE_PATH` in config
- **"UNO connection failed"**: Install `python3-uno` package
- **"Port in use"**: UNO bridge will auto-retry with different port

### Build Issues
- **"Missing module"**: Add to `--hidden-import` in `build.py`
- **"File not found"**: Add to `--add-data` in `build.py`

### Performance Issues
- **Slow startup**: Check LibreOffice installation
- **High memory**: Monitor UNO bridge for leaks

## Contributing

1. Follow the modular architecture
2. Maintain backward compatibility
3. Test on all platforms
4. Update documentation

## License

[Same as original DocAI project]

---

**Note**: This is the first native version. Report issues and feedback for continuous improvement!