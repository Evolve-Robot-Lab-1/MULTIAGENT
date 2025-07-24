#!/bin/bash

# AGENT_B Linux Setup Script
# This script installs all necessary dependencies for running AGENT_B on Linux

echo "=== AGENT_B Linux Setup ==="
echo "This script will install Chrome, system dependencies, and Python packages"
echo ""

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install essential tools
echo "Installing essential tools..."
sudo apt-get install -y wget curl gnupg

# Install Google Chrome
echo "Installing Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
    echo "✓ Chrome installed successfully"
else
    echo "✓ Chrome is already installed"
fi

# Install clipboard support for pyperclip
echo "Installing clipboard support..."
sudo apt-get install -y xclip xsel

# Install Python development headers
echo "Installing Python development headers..."
sudo apt-get install -y python3-dev python3-pip

# Install virtual display for headless environments
echo "Installing virtual display support..."
sudo apt-get install -y xvfb

# Create virtual environment (optional but recommended)
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify installations
echo ""
echo "=== Verification ==="
echo "Chrome version: $(google-chrome --version)"
echo "Python version: $(python3 --version)"
echo "Pip version: $(pip --version)"

# Check if running in headless environment
if [ -z "$DISPLAY" ]; then
    echo ""
    echo "⚠️  No display detected. You'll need to use run_headless.sh to start the application."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start AGENT_B:"
echo "1. If you have a display: python webui.py"
echo "2. If running headless: ./run_headless.sh"
echo ""
echo "Default URL: http://127.0.0.1:7788"