#!/bin/bash
# Quick start script for DocAI with LibreOffice UNO

echo "🚀 DocAI Quick Start Script"
echo "=========================="

# Navigate to project directory
cd "$(dirname "$0")"

# Set environment variables
echo "📦 Setting environment variables..."
export SAL_DISABLE_JAVALDX=1
export SAL_USE_VCLPLUGIN=gen
export SAL_DISABLE_OPENCL=1
export PYTHONPATH=/usr/lib/libreoffice/program:$PYTHONPATH

# Kill existing processes
echo "🔧 Cleaning up existing processes..."
pkill -f "python3 main_copy.py" 2>/dev/null || true
pkill -f soffice 2>/dev/null || true
pkill -f libreoffice 2>/dev/null || true
sleep 2

# Clean temporary files
echo "🧹 Cleaning temporary files..."
rm -rf /tmp/uno_convert_* 2>/dev/null || true

# Test UNO setup
echo "🧪 Testing LibreOffice UNO setup..."
python3 -c "import uno" 2>/dev/null && echo "✅ UNO module available" || echo "❌ UNO module not found"

# Check LibreOffice
libreoffice --version 2>/dev/null && echo "✅ LibreOffice installed" || echo "❌ LibreOffice not found"

# Start server
echo ""
echo "🌐 Starting DocAI server on http://127.0.0.1:8090"
echo "Press Ctrl+C to stop"
echo "============================"
echo ""

# Run the server
python3 main_copy.py 2>&1 | tee server_quickstart.log