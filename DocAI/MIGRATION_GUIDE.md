# DocAI Migration Guide

This guide walks you through migrating from the old monolithic DocAI system to the new refactored architecture.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL (for production) or SQLite (for development)
- Redis (optional, for caching)
- Virtual environment activated

## Migration Steps

### Step 1: Backup Current System

Before starting, backup your current data:

```bash
# Backup uploads directory
cp -r uploads uploads_backup_$(date +%Y%m%d)

# Backup any chat history or session data
cp chat_histories.json chat_histories_backup.json 2>/dev/null || true
```

### Step 2: Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set:
# - GROQ_API_KEY
# - DATABASE_URI (optional, defaults to SQLite)
# - FLASK_SECRET_KEY (generate a secure key)
```

### Step 4: Initialize Database

```bash
# Create database tables
python manage.py init

# Or if using Alembic migrations:
alembic upgrade head
```

### Step 5: Run Migration Script

The migration script handles:
- Creating default users
- Migrating documents from file system
- Importing chat histories
- Preserving RAG index data

```bash
# First, do a dry run to see what will be migrated
python migrate_to_new_system.py --old-path ./uploads --dry-run

# If everything looks good, run the actual migration
python migrate_to_new_system.py --old-path ./uploads
```

### Step 6: Update Frontend

Update frontend files to use new API endpoints:

```bash
# Dry run first
python scripts/update_frontend.py --dry-run

# Apply changes
python scripts/update_frontend.py
```

### Step 7: Verify Migration

```bash
# Check database
python manage.py shell
>>> from app.database.models import Document, User
>>> Document.query.count()  # Should show migrated documents
>>> User.query.count()      # Should show created users
```

## API Changes

### Authentication

The new system requires authentication. Default API keys:
- Demo: `demo-api-key-12345`
- Admin: `admin-api-key-12345` (change in production!)

Add to request headers:
```javascript
headers: {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
}
```

### Endpoint Changes

| Old Endpoint | New Endpoint |
|--------------|--------------|
| `/api/query_stream` | `/api/v1/chat/stream` |
| `/rag/upload` | `/api/v1/documents` |
| `/rag/status` | `/api/v1/documents/rag/status` |
| `/api/agent-status` | `/api/v1/agents/status` |

### Response Format

New standardized response format:
```json
{
    "status": "success",
    "data": { ... },
    "message": "Optional message",
    "metadata": { ... },
    "timestamp": "2024-01-08T10:30:00Z",
    "request_id": "uuid"
}
```

## Running Both Systems

During migration, you can run both systems:

```bash
# Terminal 1: Old system (port 8090)
python main_copy.py

# Terminal 2: New system (port 8091)
PORT=8091 python main.py
```

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t docai:latest .

# Run with docker-compose
docker-compose up -d
```

### Using systemd

Create `/etc/systemd/system/docai.service`:
```ini
[Unit]
Description=DocAI Document Intelligence Platform
After=network.target postgresql.service

[Service]
Type=exec
User=docai
WorkingDirectory=/opt/docai
Environment="PATH=/opt/docai/venv/bin"
ExecStart=/opt/docai/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Database errors**: Check DATABASE_URI in .env
3. **Permission errors**: Check file permissions on upload directories
4. **API authentication errors**: Verify API key in headers

### Rollback Plan

If migration fails:
1. Stop new system
2. Restore from backups
3. Continue using old system
4. Check logs for errors

### Getting Help

- Check logs in `logs/app.log` and `logs/error.log`
- Run tests: `pytest tests/`
- Enable debug mode: `DEBUG=True` in .env

## Post-Migration Checklist

- [ ] All documents accessible in new system
- [ ] Chat functionality working
- [ ] Authentication configured
- [ ] Frontend updated and tested
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] SSL/TLS certificates installed
- [ ] Rate limiting enabled
- [ ] Error tracking configured

## Next Steps

1. Set up monitoring (Prometheus/Grafana)
2. Configure automated backups
3. Implement caching with Redis
4. Set up CI/CD pipeline
5. Load test the system

For production configuration, see `.env.production.template`.