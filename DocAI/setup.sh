#!/bin/bash

# DocAI Development Environment Setup
# Choose your preferred isolated development option

echo "========================================"
echo "    DocAI Development Environment"
echo "========================================"
echo ""
echo "Choose your development setup:"
echo "1. Docker     - Containerized development (recommended)"
echo "2. Vagrant    - Virtual machine development"
echo "3. Git + Local - Version control with local development"
echo "4. Exit"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Setting up Docker development environment..."
        echo ""
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker is not installed. Please install Docker first:"
            echo "   https://docs.docker.com/get-docker/"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
            echo "   https://docs.docker.com/compose/install/"
            exit 1
        fi
        
        # Create .env file if it doesn't exist
        if [ ! -f .env ]; then
            echo "Creating .env file..."
            cat > .env << EOL
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
EOL
            echo "⚠️  Please edit .env file with your API keys"
        fi
        
        # Create required directories
        mkdir -p uploads/documents uploads/embeddings uploads/processed models
        
        echo "Building Docker container..."
        docker-compose build
        
        echo ""
        echo "✅ Docker setup complete!"
        echo ""
        echo "To start the application:"
        echo "  docker-compose up"
        echo ""
        echo "To stop the application:"
        echo "  docker-compose down"
        echo ""
        echo "Access the application at: http://localhost:8080"
        ;;
        
    2)
        echo "Setting up Vagrant development environment..."
        echo ""
        
        # Check if Vagrant is installed
        if ! command -v vagrant &> /dev/null; then
            echo "❌ Vagrant is not installed. Please install Vagrant first:"
            echo "   https://www.vagrantup.com/downloads"
            exit 1
        fi
        
        # Check if VirtualBox is installed
        if ! command -v vboxmanage &> /dev/null; then
            echo "❌ VirtualBox is not installed. Please install VirtualBox first:"
            echo "   https://www.virtualbox.org/wiki/Downloads"
            exit 1
        fi
        
        # Create .env file if it doesn't exist
        if [ ! -f .env ]; then
            echo "Creating .env file..."
            cat > .env << EOL
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
EOL
            echo "⚠️  Please edit .env file with your API keys"
        fi
        
        echo "Starting Vagrant VM..."
        vagrant up
        
        echo ""
        echo "✅ Vagrant setup complete!"
        echo ""
        echo "To access the VM:"
        echo "  vagrant ssh"
        echo ""
        echo "To start the application (inside VM):"
        echo "  ./run.sh"
        echo ""
        echo "To stop the VM:"
        echo "  vagrant halt"
        echo ""
        echo "Access the application at: http://localhost:8080"
        ;;
        
    3)
        echo "Setting up Git + Local development environment..."
        echo ""
        
        # Check if Git is installed
        if ! command -v git &> /dev/null; then
            echo "❌ Git is not installed. Please install Git first:"
            echo "   https://git-scm.com/downloads"
            exit 1
        fi
        
        # Check if Python is installed
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python 3 is not installed. Please install Python 3 first:"
            echo "   https://www.python.org/downloads/"
            exit 1
        fi
        
        # Initialize Git repository
        echo "Initializing Git repository..."
        git init
        
        # Configure Git user
        echo "Configuring Git user..."
        git config user.name "Evolve-Robot-Lab-1"
        read -p "Enter your email address: " email
        git config user.email "$email"
        
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
        
        # Create .env file if it doesn't exist
        if [ ! -f .env ]; then
            echo "Creating .env file..."
            cat > .env << EOL
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
EOL
            echo "⚠️  Please edit .env file with your API keys"
        fi
        
        # Create virtual environment
        echo "Creating Python virtual environment..."
        python3 -m venv docai_env
        
        # Activate virtual environment and install dependencies
        echo "Installing dependencies..."
        source docai_env/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        # Download NLTK data
        echo "Downloading NLTK data..."
        python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
        
        # Create required directories
        mkdir -p uploads/documents uploads/embeddings uploads/processed models
        
        # Create .gitkeep files
        touch uploads/documents/.gitkeep
        touch uploads/embeddings/.gitkeep
        touch uploads/processed/.gitkeep
        touch models/.gitkeep
        
        # Initial commit
        git add .
        git commit -m "Initial commit: DocAI project setup"
        
        echo ""
        echo "✅ Git + Local setup complete!"
        echo ""
        echo "To start the application:"
        echo "  source docai_env/bin/activate"
        echo "  python main_copy.py"
        echo ""
        echo "To deactivate virtual environment:"
        echo "  deactivate"
        echo ""
        echo "Access the application at: http://localhost:8080"
        ;;
        
    4)
        echo "Exiting setup..."
        exit 0
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again and choose 1-4."
        exit 1
        ;;
esac