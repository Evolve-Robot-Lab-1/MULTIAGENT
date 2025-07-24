# DocAI - Document Intelligence Platform

DocAI is a full-stack document intelligence platform that combines document processing, vector search (RAG), and AI-powered chat. It uses Flask backend with vanilla JavaScript frontend.

## Features

- 📄 **Multi-format Document Processing**: PDF, DOCX, TXT support with LibreOffice integration
- 🔍 **Vector Search (RAG)**: FAISS-powered semantic search across documents
- 🤖 **Multi-AI Provider Support**: Groq, OpenAI, Anthropic Claude, Google Gemini
- 💬 **Interactive Chat Interface**: Real-time streaming responses with document context
- 🎯 **Smart Document Viewer**: Integrated viewer with chat overlay
- 🔄 **Persistent Memory**: Document embeddings cached for fast retrieval

## Architecture

- **Backend**: Flask with Python 3.8+
- **Frontend**: Vanilla JavaScript with responsive design
- **Vector Store**: FAISS with HuggingFace embeddings
- **Document Processing**: LibreOffice UNO, PyPDF2, python-docx
- **AI Integration**: Multi-provider API support

## 🚀 Quick Start

### Automated Setup (Recommended)

Run the interactive setup script to choose your preferred development environment:

```bash
./setup.sh
```

This will guide you through three isolated development options:

---

## Development Environment Options

### Option 1: 🐳 Docker (Recommended)

**Best for**: Cross-platform development, easy deployment, isolated environment

```bash
# Quick start
docker-compose up --build

# Access at http://localhost:8080
```

**Advantages:**
- Complete isolation from host system
- Consistent environment across all platforms
- Easy cleanup and reset
- Includes all dependencies (LibreOffice, Python, etc.)

**Commands:**
```bash
# Start application
docker-compose up

# Start in background
docker-compose up -d

# Stop application
docker-compose down

# Rebuild container
docker-compose build --no-cache

# View logs
docker-compose logs -f
```

---

### Option 2: 📦 Vagrant (VM-based)

**Best for**: Full Linux environment simulation, development flexibility

```bash
# Start VM
vagrant up

# SSH into VM
vagrant ssh

# Run application
./run.sh

# Access at http://localhost:8080
```

**Advantages:**
- Full Ubuntu 22.04 environment
- Persistent development environment
- Direct file system access
- Ideal for complex development workflows

**Commands:**
```bash
# Start VM
vagrant up

# SSH into VM
vagrant ssh

# Stop VM
vagrant halt

# Destroy VM
vagrant destroy

# Reload VM configuration
vagrant reload
```

---

### Option 3: 🔧 Git + Local Development

**Best for**: Direct development, version control, local environment

```bash
# Initialize and setup
git init
python3 -m venv docai_env
source docai_env/bin/activate
pip install -r requirements.txt

# Run application
python main_copy.py

# Access at http://localhost:8080
```

**Advantages:**
- Direct access to code
- Full Git version control
- Fast development cycle
- Native performance

**Requirements:**
- Python 3.8+
- LibreOffice (for document conversion)
- Git

---

## Configuration

Create a `.env` file with your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
```

## Usage

1. **Upload Documents**: Use the upload interface to add PDF, DOCX, or TXT files
2. **Processing**: Documents are automatically processed and embedded for search
3. **Chat Interface**: Ask questions about your documents using natural language
4. **AI Model Selection**: Choose from multiple AI providers via the dropdown
5. **Document Viewer**: View documents with integrated chat overlay

## API Endpoints

- `POST /rag/upload` - Upload and process documents
- `GET /api/query_stream` - Stream chat responses with document context
- `GET /api/documents` - List processed documents
- `DELETE /api/documents/<filename>` - Remove documents

## Project Structure

```
docai/
├── main_copy.py           # Flask application entry point
├── rag_handler.py         # Document processing and RAG pipeline
├── config.py              # Configuration and API key management
├── setup.sh              # Interactive setup script
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker Compose configuration
├── Vagrantfile           # Vagrant VM configuration
├── static2.0/
│   ├── app.js            # Frontend JavaScript
│   ├── stylenew.css      # Styles
│   └── indexf.html       # Main HTML template
├── uploads/              # Document storage
├── models/               # ML model cache
└── requirements.txt      # Python dependencies
```

## Development

### Adding New Document Formats

1. Update `ALLOWED_EXTENSIONS` in `rag_handler.py`
2. Add processing logic in the `process_documents()` method
3. Test with sample files

### Adding New AI Providers

1. Add API configuration in `config.py`
2. Implement provider logic in `/api/query_stream` route
3. Update frontend dropdown in `static2.0/app.js`

### Customizing the Interface

- Edit `static2.0/stylenew.css` for styling changes
- Modify `static2.0/app.js` for functionality updates
- Update `static2.0/indexf.html` for structural changes

## Troubleshooting

### Common Issues

1. **LibreOffice Conversion Errors**: Ensure LibreOffice is properly installed
2. **NLTK Download Errors**: Run the NLTK download commands manually
3. **API Key Errors**: Verify your API keys in the `.env` file
4. **Port Conflicts**: Change the port in `main_copy.py` if 8080 is occupied

### Environment-Specific Issues

**Docker:**
- Check container logs: `docker-compose logs`
- Rebuild if needed: `docker-compose build --no-cache`

**Vagrant:**
- Increase VM memory if needed in `Vagrantfile`
- Re-provision: `vagrant provision`

**Local:**
- Activate virtual environment: `source docai_env/bin/activate`
- Install LibreOffice separately on your system

### Logs

Check these files for debugging:
- `app.log` - Application logs
- `error.log` - Error logs
- Browser console for frontend issues

## Platform Compatibility

| Platform | Docker | Vagrant | Local |
|----------|--------|---------|-------|
| Windows  | ✅     | ✅      | ⚠️*   |
| macOS    | ✅     | ✅      | ✅    |
| Linux    | ✅     | ✅      | ✅    |

*LibreOffice UNO integration may require additional setup on Windows

## Contributing

1. Fork the repository
2. Choose your preferred development environment
3. Create a feature branch
4. Make your changes
5. Test thoroughly across environments
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.