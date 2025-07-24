#!/bin/bash
# Migration script to move from old to new DocAI system

set -e  # Exit on error

echo "DocAI Migration Script"
echo "====================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running in DocAI directory
if [ ! -f "main.py" ] || [ ! -f "main_copy.py" ]; then
    print_error "This script must be run from the DocAI directory"
    exit 1
fi

# Step 1: Check environment
print_status "Checking environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
print_status "Python version: $python_version"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_error "Virtual environment not activated!"
    print_warning "Please activate your existing virtual environment first:"
    echo "    source venv/bin/activate  # On Linux/Mac"
    echo "    or"
    echo "    venv\\Scripts\\activate   # On Windows"
    exit 1
fi

print_status "Virtual environment detected: $VIRTUAL_ENV"

# Step 2: Check and install missing dependencies
print_status "Checking dependencies..."

# Check for new dependencies that might be missing
missing_deps=""

# Check for required packages
python -c "import sqlalchemy" 2>/dev/null || missing_deps="$missing_deps sqlalchemy"
python -c "import alembic" 2>/dev/null || missing_deps="$missing_deps alembic"
python -c "import click" 2>/dev/null || missing_deps="$missing_deps click"
python -c "import email_validator" 2>/dev/null || missing_deps="$missing_deps email-validator"

if [ -n "$missing_deps" ]; then
    print_warning "Missing dependencies detected: $missing_deps"
    print_status "Installing missing dependencies..."
    pip install $missing_deps
else
    print_status "All required dependencies are installed"
fi

# Optionally update all dependencies
read -p "Do you want to update all dependencies from requirements.txt? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install -r requirements.txt --upgrade
    print_status "Dependencies updated"
fi

# Step 3: Check configuration
print_status "Checking configuration..."

if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warning "Please edit .env file with your configuration"
        exit 1
    else
        print_error "No .env.example file found"
        exit 1
    fi
fi

# Step 4: Initialize database
print_status "Initializing database..."
python manage.py init

# Step 5: Run migration (dry run first)
print_status "Running migration in dry-run mode..."
python migrate_to_new_system.py --old-path ./uploads --dry-run

# Ask for confirmation
echo ""
read -p "Do you want to proceed with the actual migration? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Step 6: Run actual migration
    print_status "Running actual migration..."
    python migrate_to_new_system.py --old-path ./uploads
    
    # Step 7: Verify migration
    print_status "Verifying migration..."
    python -c "
from app.database import DatabaseSession
from app.database.models import Document, User
with DatabaseSession() as session:
    doc_count = session.query(Document).count()
    user_count = session.query(User).count()
    print(f'Documents in database: {doc_count}')
    print(f'Users in database: {user_count}')
"
    
    # Step 8: Update frontend configuration
    print_status "Updating frontend configuration..."
    
    # Check if we need to update API endpoints
    if grep -q "/api/query_stream" static2.0/*.js 2>/dev/null; then
        print_warning "Frontend files need to be updated to use new API endpoints"
        print_warning "Run: python scripts/update_frontend.py"
    fi
    
    print_status "Migration completed successfully!"
    
    echo ""
    echo "Next steps:"
    echo "1. Update frontend to use new API endpoints"
    echo "2. Configure authentication (API keys)"
    echo "3. Set up production environment (.env.production)"
    echo "4. Deploy with Docker or systemd"
    echo "5. Set up monitoring and backups"
    
else
    print_warning "Migration cancelled"
fi