#!/bin/bash

echo "==========================================
     AGENT_B_LINUX_NEW - Offline Mode
==========================================
"

cd "$(dirname "$0")"

# Kill any existing instances
pkill -f "webui.py" 2>/dev/null
sleep 1

# Set environment variables for offline mode
export GRADIO_ANALYTICS_ENABLED="False"
export GRADIO_SERVER_NAME="127.0.0.1"
export HF_HUB_OFFLINE="1"
export TRANSFORMERS_OFFLINE="1"
export ANONYMIZED_TELEMETRY="false"
export BROWSER_USE_TELEMETRY="false"
export PYTHONPATH="/media/erl/New Volume/ai_agent/docai_final/browser-use-main:."
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python"
export PYTHONNOUSERSITE="1"

echo "Starting application in offline mode..."
echo "Opening at: http://localhost:7788"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run with proper environment
"/media/erl/New Volume/ai_agent/docai_final/turboo_linux_new/bin/python" webui.py --ip 127.0.0.1 --port 7788