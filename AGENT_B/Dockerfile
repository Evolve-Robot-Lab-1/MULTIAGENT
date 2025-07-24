FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python and build tools
    python3.10 \
    python3.10-venv \
    python3-pip \
    python3-dev \
    build-essential \
    # Chrome dependencies
    wget \
    gnupg \
    ca-certificates \
    # Required libraries
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libdrm2 \
    libgbm1 \
    libxkbcommon0 \
    # X11 and display
    xvfb \
    x11vnc \
    fluxbox \
    # Utilities
    curl \
    unzip \
    git \
    nano \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy browser-use-main first (dependency)
COPY browser-use-main /browser-use-main

# Copy virtual environment
COPY turboo_linux_new /venv

# Copy application code
COPY AGENT_B_LINUX_NEW /app

# Set environment variables
ENV VIRTUAL_ENV=/venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/browser-use-main:/app"
ENV DISPLAY=:99
ENV RESOLUTION=1920x1080x24

# Browser and telemetry settings
ENV ANONYMIZED_TELEMETRY=false
ENV BROWSER_USE_TELEMETRY=false
ENV GRADIO_ANALYTICS_ENABLED=False
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Chrome settings
ENV CHROME_PATH=/usr/bin/google-chrome-stable
ENV CHROME_ARGS="--no-sandbox --disable-gpu --disable-dev-shm-usage"

# Create necessary directories
RUN mkdir -p /app/tmp /app/logs

# Expose ports
EXPOSE 7788
EXPOSE 5900

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Xvfb\n\
Xvfb :99 -screen 0 $RESOLUTION -ac +extension GLX +render -noreset &\n\
sleep 2\n\
\n\
# Start fluxbox window manager\n\
fluxbox &\n\
sleep 1\n\
\n\
# Optional: Start VNC server for debugging\n\
if [ "$ENABLE_VNC" = "true" ]; then\n\
    x11vnc -display :99 -forever -usepw -create &\n\
    echo "VNC server started on port 5900"\n\
fi\n\
\n\
# Start the application\n\
cd /app\n\
echo "Starting AGENT_B_LINUX_NEW on http://0.0.0.0:7788"\n\
exec python webui.py --ip 0.0.0.0 --port 7788\n\
' > /app/docker_start.sh && chmod +x /app/docker_start.sh

# Start command
CMD ["/app/docker_start.sh"]