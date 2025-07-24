#!/bin/bash

# Setup script to create a fully isolated environment for AGENT_B
# This script will install all dependencies including browser-use from local source

echo "Setting up isolated environment for AGENT_B..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create virtual environment for AGENT_B if it doesn't exist
if [ ! -d "AGENT_B/venv" ]; then
    echo "Creating virtual environment for AGENT_B..."
    python3 -m venv AGENT_B/venv
fi

# Activate virtual environment
source AGENT_B/venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install browser-use from local source
echo "Installing browser-use from local source..."
BROWSER_USE_PATH="../browser-use-main"
if [ -d "$BROWSER_USE_PATH" ]; then
    pip install -e "$BROWSER_USE_PATH"
else
    echo "ERROR: browser-use source not found at $BROWSER_USE_PATH"
    echo "Please ensure browser-use-main folder exists in the parent directory"
    exit 1
fi

# Install AGENT_B requirements
echo "Installing AGENT_B requirements..."
cd AGENT_B
pip install -r requirements.txt

# Create a requirements_frozen.txt with all installed packages
echo "Creating requirements_frozen.txt with all dependencies..."
pip freeze > requirements_frozen.txt

echo "Setup complete! Virtual environment is fully isolated."
echo ""
echo "To activate the environment, run:"
echo "  source AGENT_B/venv/bin/activate"
echo ""
echo "To run AGENT_B:"
echo "  cd AGENT_B"
echo "  python webui.py"