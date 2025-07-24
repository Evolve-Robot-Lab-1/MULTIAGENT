# DocAI Refactoring Guide

## Overview

This document describes the refactored architecture of the DocAI application. The refactoring transforms a monolithic 1560-line Flask application into a well-structured, modular system following modern software engineering best practices.

## New Project Structure

```
DocAI/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── api/
│   │   ├── v1/                  # API v1 endpoints
│   │   │   ├── documents.py     # Document endpoints
│   │   │   ├── chat.py          # Chat endpoints
│   │   │   └── agents.py        # Agent management endpoints
│   │   └── middleware/
│   │       └── error_handler.py # Global error handling
│   ├── core/
│   │   ├── config.py            # Centralized configuration
│   │   ├── exceptions.py        # Custom exception hierarchy
│   │   └── logging.py           # Structured logging
│   ├── models/
│   │   ├── api.py              # API request/response models
│   │   └── document.py         # Document data models
│   ├── services/
│   │   ├── base.py             # Base service & DI container
│   │   ├── document_service.py  # Document processing logic
│   │   ├── chat_service.py      # Chat management
│   │   ├── rag_service.py       # RAG functionality
│   │   └── agent_manager.py     # External agent management
│   └── utils/
│       └── converters/          # Document converters
│           ├── base.py          # Converter interface
│           ├── docx_converter.py
│           ├── pdf_converter.py
│           └── text_converter.py
├── static2.0/                   # Frontend assets (unchanged)
├── main.py                      # New slim entry point
└── main_copy.py                 # Original monolithic file
```

## Key Improvements

### 1. Configuration Management
- **Before**: Environment variables scattered throughout code
- **After**: Centralized `Config` class with validation and type safety

```python
# Old way
groq_api_key = os.environ.get("GROQ_API_KEY")

# New way
config = Config.from_env()
groq_api_key = config.ai.groq_api_key
```

### 2. Service Layer Architecture
- **Before**: Business logic mixed with route handlers
- **After**: Clean separation with service classes

```python
# Old way (in route handler)
@app.route('/upload', methods=['POST'])
def upload():
    # 100+ lines of file handling, validation, processing...

# New way
@documents_bp.route('', methods=['POST'])
async def upload_document():
    result = await doc_service.upload_document(file, request)
    return APIResponse.success(result.data)
```

### 3. Error Handling
- **Before**: Inconsistent try/catch blocks
- **After**: Centralized error handling with custom exceptions

```python
# Exception hierarchy
DocAIException
├── DocumentException
│   ├── DocumentNotFoundError
│   ├── DocumentProcessingError
│   └── UnsupportedFileTypeError
├── AIException
│   └── AIProviderError
└── AgentException
    └── AgentConnectionError
```

### 4. API Standardization
- **Before**: Mixed response formats
- **After**: Consistent API responses with versioning

```python
# Standardized response format
{
    "status": "success",
    "data": {...},
    "message": "Document uploaded successfully",
    "metadata": {...},
    "timestamp": "2024-01-08T10:30:00Z",
    "request_id": "uuid"
}
```

### 5. Dependency Injection
- **Before**: Direct instantiation and global variables
- **After**: IoC container with proper lifecycle management

```python
# Service registration
app.container.register(DocumentService)
app.container.register(ChatService)

# Service injection
doc_service = app.container.get(DocumentService)
```

## Migration Guide

### Phase 1: Run Both Systems (Week 1)
1. Keep `main_copy.py` running on port 8090
2. Run new `main.py` on port 8091
3. Use nginx/proxy to route traffic

### Phase 2: Gradual Migration (Week 2-3)
1. Update frontend to use `/api/v1/` endpoints
2. Monitor for issues
3. Fix any compatibility problems

### Phase 3: Complete Cutover (Week 4)
1. Update all clients to new endpoints
2. Shut down old system
3. Move new system to port 8090

## Testing Strategy

### Unit Tests
```python
# test_document_service.py
async def test_upload_document():
    service = DocumentService(test_config)
    result = await service.upload_document(mock_file, request)
    assert result.success
```

### Integration Tests
```python
# test_api_documents.py
async def test_document_upload_api():
    response = await client.post('/api/v1/documents', 
                                files={'document': test_file})
    assert response.status_code == 201
```

## Configuration Examples

### Development
```env
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
GROQ_API_KEY=your-dev-key
```

### Production
```env
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
GROQ_API_KEY=your-prod-key
DATABASE_URI=postgresql://...
```

## API Endpoint Mapping

| Old Endpoint | New Endpoint | Notes |
|-------------|--------------|-------|
| `/rag/upload` | `/api/v1/documents` | POST |
| `/rag/status` | `/api/v1/documents/rag/status` | GET |
| `/api/query_stream` | `/api/v1/chat/stream` | POST |
| `/api/agent-status` | `/api/v1/agents/status` | GET |

## Future Enhancements

1. **Database Integration**
   - Replace in-memory storage with PostgreSQL
   - Add SQLAlchemy models
   - Implement proper migrations

2. **Authentication & Authorization**
   - Add JWT authentication
   - Implement role-based access control
   - Add API key management

3. **Monitoring & Observability**
   - Add Prometheus metrics
   - Implement distributed tracing
   - Enhanced logging with correlation IDs

4. **Performance Optimization**
   - Add Redis caching layer
   - Implement connection pooling
   - Add async task queue (Celery)

5. **Testing & CI/CD**
   - Achieve 80%+ test coverage
   - Add automated integration tests
   - Implement blue-green deployments

## Conclusion

This refactoring provides a solid foundation for the DocAI application to scale and evolve. The modular architecture makes it easy to:
- Add new features without touching existing code
- Test components in isolation
- Deploy and scale services independently
- Maintain and debug the application

The clean separation of concerns and proper abstractions ensure that the codebase remains maintainable as it grows.