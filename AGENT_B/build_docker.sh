#!/bin/bash

# Build script for Docker image

echo "==========================================
Building AGENT_B_LINUX_NEW Docker Image
==========================================
"

# Get the parent directory
PARENT_DIR=$(dirname "$(pwd)")

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "Error: Dockerfile not found. Run this script from AGENT_B_LINUX_NEW directory."
    exit 1
fi

# Check if required directories exist
if [ ! -d "$PARENT_DIR/browser-use-main" ]; then
    echo "Error: browser-use-main directory not found at $PARENT_DIR/browser-use-main"
    exit 1
fi

if [ ! -d "$PARENT_DIR/turboo_linux_new" ]; then
    echo "Error: turboo_linux_new directory not found at $PARENT_DIR/turboo_linux_new"
    exit 1
fi

echo "Building Docker image..."
echo "Context directory: $PARENT_DIR"

# Build the image
cd "$PARENT_DIR"
docker build -f AGENT_B_LINUX_NEW/Dockerfile -t agent-b-linux:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Docker image built successfully!"
    echo ""
    echo "To run the container:"
    echo "  docker run -d -p 7788:7788 --name agent-b --shm-size=2gb agent-b-linux:latest"
    echo ""
    echo "Or use docker-compose:"
    echo "  docker-compose -f AGENT_B_LINUX_NEW/docker-compose.yml up -d"
    echo ""
    echo "Access the application at: http://localhost:7788"
else
    echo "❌ Docker build failed!"
    exit 1
fi