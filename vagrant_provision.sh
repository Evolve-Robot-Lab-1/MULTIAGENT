#!/bin/bash
# Vagrant provision script for DocAI + AGENT_B

set -e

echo "========================================="
echo "Starting DocAI + AGENT_B provisioning..."
echo "========================================="

# Update system
echo "Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y -qq \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    build-essential \
    curl \
    wget \
    git \
    libssl-dev \
    libffi-dev \
    python3-setuptools \
    libjpeg-dev \
    zlib1g-dev \
    xvfb \
    x11vnc \
    fluxbox \
    chromium-browser \
    chromium-chromedriver

# Install LibreOffice and UNO bindings
echo "Installing LibreOffice with UNO bindings..."
sudo apt-get install -y -qq \
    libreoffice \
    libreoffice-script-provider-python \
    python3-uno \
    libreoffice-java-common

# Create necessary directories
echo "Setting up project structure..."
cd /home/vagrant/docai_final

# Recreate virtual environment if it doesn't exist properly
if [ ! -f "turboo_linux_new/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3.10 -m venv turboo_linux_new
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source turboo_linux_new/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install browser-use from local source
echo "Installing browser-use..."
if [ -d "browser_use" ]; then
    pip install -e ./browser_use
fi

# Install AGENT_B requirements
echo "Installing AGENT_B dependencies..."
if [ -f "AGENT_B/requirements.txt" ]; then
    pip install -r AGENT_B/requirements.txt
fi

# Install DocAI requirements if they exist
echo "Installing DocAI dependencies..."
if [ -f "DocAI/requirements.txt" ]; then
    pip install -r DocAI/requirements.txt
fi

# Install additional requirements
if [ -f "DocAI/requirements_complete.txt" ]; then
    pip install -r DocAI/requirements_complete.txt
fi

# Setup LibreOffice Python path
echo "Configuring LibreOffice Python bindings..."
cat > /home/vagrant/docai_final/setup_uno.sh << 'EOF'
#!/bin/bash
# Setup UNO Python path
export PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH
export URE_BOOTSTRAP="vnd.sun.star.pathname:/usr/lib/libreoffice/program/fundamentalrc"
EOF
chmod +x /home/vagrant/docai_final/setup_uno.sh

# Create startup scripts
echo "Creating startup scripts..."

# AGENT_B startup script
cat > /home/vagrant/docai_final/start_agent_b.sh << 'EOF'
#!/bin/bash
cd /home/vagrant/docai_final
source turboo_linux_new/bin/activate
source setup_uno.sh
cd AGENT_B
python webui.py --ip 0.0.0.0 --port 7788
EOF
chmod +x /home/vagrant/docai_final/start_agent_b.sh

# DocAI startup script
cat > /home/vagrant/docai_final/start_docai.sh << 'EOF'
#!/bin/bash
cd /home/vagrant/docai_final
source turboo_linux_new/bin/activate
source setup_uno.sh
cd DocAI
python main_copy.py
EOF
chmod +x /home/vagrant/docai_final/start_docai.sh

# Create a combined startup script
cat > /home/vagrant/docai_final/start_all.sh << 'EOF'
#!/bin/bash
echo "Starting all services..."

# Start LibreOffice in headless mode
soffice --headless --accept="socket,host=localhost,port=2002;urp;" --nofirststartwizard &

# Give LibreOffice time to start
sleep 5

# Start AGENT_B in background
cd /home/vagrant/docai_final
./start_agent_b.sh &

# Start DocAI
./start_docai.sh &

echo "All services started!"
echo "AGENT_B: http://localhost:7788"
echo "DocAI: http://localhost:8090"
EOF
chmod +x /home/vagrant/docai_final/start_all.sh

# Set proper permissions
chown -R vagrant:vagrant /home/vagrant/docai_final

echo "========================================="
echo "Provisioning completed successfully!"
echo "========================================="
echo ""
echo "To start AGENT_B:"
echo "  ./start_agent_b.sh"
echo ""
echo "To start DocAI:"
echo "  ./start_docai.sh"
echo ""
echo "To start all services:"
echo "  ./start_all.sh"
echo "========================================="