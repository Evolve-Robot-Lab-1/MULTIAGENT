#!/bin/bash

# Git Setup Script for DocAI Project
# Sets up Git repository with Evolve-Robot-Lab-1 credentials

echo "========================================"
echo "    DocAI Git Repository Setup"
echo "========================================"
echo ""

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   https://git-scm.com/downloads"
    exit 1
fi

# Check if already a Git repository
if [ -d .git ]; then
    echo "⚠️  Git repository already exists."
    read -p "Do you want to reconfigure Git settings? (y/n): " reconfigure
    if [[ $reconfigure != "y" && $reconfigure != "Y" ]]; then
        echo "Exiting..."
        exit 0
    fi
else
    # Initialize Git repository
    echo "Initializing Git repository..."
    git init
fi

# Configure Git user
echo "Configuring Git user..."
git config user.name "Evolve-Robot-Lab-1"

# Get email address
read -p "Enter your email address: " email
git config user.email "$email"

# Set default branch to main
git config init.defaultBranch main

# Display current configuration
echo ""
echo "✅ Git configuration complete!"
echo ""
echo "Current Git settings:"
echo "  User: $(git config user.name)"
echo "  Email: $(git config user.email)"
echo "  Default branch: $(git config init.defaultBranch)"
echo ""

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
docai_env/
venv/
ENV/

# Flask
instance/
.webassets-cache

# Logs
*.log
app.log
error.log

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
uploads/documents/*
uploads/embeddings/*
uploads/processed/*
models/*
!models/.gitkeep
debug_raw_output_*.html
conversion_stats.json

# Vagrant
.vagrant/
*.box

# Docker
docker-compose.override.yml

# Keep directories
!uploads/documents/.gitkeep
!uploads/embeddings/.gitkeep
!uploads/processed/.gitkeep
EOL
fi

# Create .gitkeep files for empty directories
echo "Creating directory structure..."
mkdir -p uploads/documents uploads/embeddings uploads/processed models
touch uploads/documents/.gitkeep
touch uploads/embeddings/.gitkeep
touch uploads/processed/.gitkeep
touch models/.gitkeep

# Add files to staging
echo "Adding files to Git..."
git add .

# Check if there are any changes to commit
if git diff --staged --quiet; then
    echo "No changes to commit."
else
    # Create initial commit
    echo "Creating initial commit..."
    git commit -m "Initial commit: DocAI project setup

- Document intelligence platform with Flask backend
- Multi-format document processing (PDF, DOCX, TXT)
- Vector search with RAG implementation
- Multi-AI provider support (Groq, OpenAI, Gemini)
- Interactive chat interface with document context
- Docker and Vagrant deployment options

🚀 Generated with Evolve-Robot-Lab-1"
fi

echo ""
echo "🎉 Git repository setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a remote repository on GitHub/GitLab"
echo "2. Add remote origin:"
echo "   git remote add origin <your-repository-url>"
echo "3. Push to remote:"
echo "   git push -u origin main"
echo ""
echo "To check status: git status"
echo "To make changes: git add . && git commit -m 'Your message'"