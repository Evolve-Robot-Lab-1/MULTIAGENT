# 🐧 AGENT_B Linux Setup Guide

## System Requirements

- Ubuntu 20.04+ or Debian 10+ (other distributions should work with minor adjustments)
- Python 3.8 or higher
- At least 4GB RAM
- 2GB free disk space

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to the AGENT_B_LINUX_NEW directory
cd AGENT_B_LINUX_NEW

# Make setup script executable and run it
chmod +x setup_linux.sh
./setup_linux.sh
```

This script will automatically install:
- Google Chrome browser
- Clipboard support (xclip/xsel) for pyperclip
- Python development headers
- Virtual display support (Xvfb)
- All Python dependencies

### 2. Configure API Keys

Edit the `.env` file with your API keys:
```bash
nano .env
```

At minimum, configure one LLM provider (e.g., Google Gemini is set by default).

### 3. Run AGENT_B

#### Option A: With Display (Desktop Linux)
```bash
python webui.py
```

#### Option B: Headless Server (No Display)
```bash
./run_headless.sh
```

#### Custom Options
```bash
# Run on different port
python webui.py --port 8080

# Run on all interfaces (for remote access)
python webui.py --ip 0.0.0.0

# With custom theme
python webui.py --theme Monochrome
```

## Manual Installation (if setup script fails)

### Install Chrome
```bash
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt-get update
sudo apt-get install -y google-chrome-stable
```

### Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    xclip \
    xsel \
    xvfb
```

### Install Python Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Docker Support (Alternative)

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    xclip \
    xsel \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 7788
CMD ["./run_headless.sh"]
```

Build and run:
```bash
docker build -t agent-b .
docker run -p 7788:7788 agent-b
```

## Common Issues & Solutions

### 1. Chrome Crashes
**Solution**: Ensure `--no-sandbox` flag is present (already configured in webui.py)

### 2. Clipboard Error
**Error**: `Pyperclip could not find a copy/paste mechanism`
**Solution**: 
```bash
sudo apt-get install xclip xsel
# For SSH sessions:
export DISPLAY=:0
```

### 3. No Display Variable
**Error**: `Error: no DISPLAY environment variable specified`
**Solution**: Use `./run_headless.sh` instead of `python webui.py`

### 4. Permission Denied
**Solution**:
```bash
chmod +x setup_linux.sh run_headless.sh
```

### 5. Virtual Environment Issues
**Solution**:
```bash
deactivate  # If in another venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Performance Optimization

### For VPS/Cloud Servers
1. Increase swap if RAM < 4GB:
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

2. Optimize Chrome flags (already included):
- `--disable-gpu`
- `--disable-dev-shm-usage`
- `--no-sandbox`

### For Production Use
1. Use systemd service:
```bash
sudo nano /etc/systemd/system/agent-b.service
```

```ini
[Unit]
Description=AGENT_B Browser Automation
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/AGENT_B_LINUX_NEW
Environment="PATH=/path/to/AGENT_B_LINUX_NEW/venv/bin"
ExecStart=/path/to/AGENT_B_LINUX_NEW/run_headless.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable agent-b
sudo systemctl start agent-b
```

## Security Considerations

1. **Firewall**: If exposing to network, limit access:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 7788
```

2. **Reverse Proxy**: Use nginx for HTTPS:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:7788;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
```

## Testing

Run the test suite:
```bash
# Basic functionality
python tests/test_screenshot.py

# Full integration test
python tests/test_integration.py

# CAPTCHA handling test
python tests/test_captcha.py
```

## Linux-Specific Features

1. **Resolution Control**: Set custom resolution in `.env`:
```bash
RESOLUTION=1920x1080x24
RESOLUTION_WIDTH=1920
RESOLUTION_HEIGHT=1080
```

2. **Headless Mode**: Always runs headless on Linux (configured in webui.py)

3. **Resource Limits**: Chrome is configured with Linux-optimized flags

## Support

For Linux-specific issues:
1. Check Chrome installation: `google-chrome --version`
2. Verify display: `echo $DISPLAY`
3. Test xvfb: `xvfb-run -a echo "success"`
4. Review logs: Check console output for errors

## Summary

AGENT_B on Linux offers:
- ✅ Full headless operation
- ✅ Automatic CAPTCHA solving
- ✅ Enhanced anti-detection
- ✅ Resource-efficient Chrome configuration
- ✅ Virtual display support for GUI-less servers
- ✅ Production-ready with systemd integration