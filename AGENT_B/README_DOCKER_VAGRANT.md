# AGENT_B_LINUX_NEW - Docker & Vagrant Deployment

This document explains how to run AGENT_B_LINUX_NEW using Docker or Vagrant on any system (Windows, Mac, Linux).

## 🐳 Docker Deployment

### Prerequisites
- Docker installed on your system
- Docker Compose (optional, for easier management)

### Quick Start

#### Option 1: Using Docker Compose (Recommended)
```bash
# From the BROWSER AGENT directory
cd "/media/erl/New Volume/ai_agent/BROWSER AGENT"

# Build and start the container
docker-compose -f AGENT_B_LINUX_NEW/docker-compose.yml up -d

# View logs
docker-compose -f AGENT_B_LINUX_NEW/docker-compose.yml logs -f

# Stop the container
docker-compose -f AGENT_B_LINUX_NEW/docker-compose.yml down
```

#### Option 2: Using Docker directly
```bash
# Build the image
cd "/media/erl/New Volume/ai_agent/BROWSER AGENT"
docker build -f AGENT_B_LINUX_NEW/Dockerfile -t agent-b-linux .

# Run the container
docker run -d \
  --name agent-b \
  -p 7788:7788 \
  -e GOOGLE_API_KEY=AIzaSyBQ0YV0bAUdGx19LTncuo_uWMAjp1oAfYg \
  -e GEMINI_API_KEY=AIzaSyCsdm6uvSZB0ibxnnaWB1aD4vUvVsS74Sc \
  --shm-size=2gb \
  agent-b-linux

# View logs
docker logs -f agent-b

# Stop the container
docker stop agent-b
docker rm agent-b
```

### Accessing the Application
- Open your browser to: **http://localhost:7788**
- The browser automation runs inside the container
- Your local browser is just viewing the web interface

### Advanced Options

#### Enable VNC for debugging
```bash
docker run -d \
  --name agent-b \
  -p 7788:7788 \
  -p 5900:5900 \
  -e ENABLE_VNC=true \
  --shm-size=2gb \
  agent-b-linux
```
Then connect with VNC viewer to `localhost:5900`

#### Using custom API keys
Create a `.env` file:
```env
OPENAI_API_KEY=your_actual_key
ANTHROPIC_API_KEY=your_actual_key
GOOGLE_API_KEY=AIzaSyBQ0YV0bAUdGx19LTncuo_uWMAjp1oAfYg
GEMINI_API_KEY=AIzaSyCsdm6uvSZB0ibxnnaWB1aD4vUvVsS74Sc
```

Then run with:
```bash
docker-compose --env-file .env -f AGENT_B_LINUX_NEW/docker-compose.yml up -d
```

## 📦 Vagrant Deployment

### Prerequisites
- Vagrant installed
- VirtualBox installed

### Quick Start

```bash
cd "/media/erl/New Volume/ai_agent/BROWSER AGENT/AGENT_B_LINUX_NEW"

# Start the VM
vagrant up

# SSH into the VM
vagrant ssh

# Inside the VM, start the agent
start-agent

# Or use systemd
sudo systemctl start agent-b
```

### Accessing the Application
- Open your browser to: **http://localhost:7788**
- Or use the private IP: **http://192.168.56.10:7788**

### Vagrant Commands
```bash
# Start VM
vagrant up

# Stop VM
vagrant halt

# Restart VM
vagrant reload

# SSH into VM
vagrant ssh

# Destroy VM
vagrant destroy

# Check status
vagrant status
```

### Inside the Vagrant VM
```bash
# Start agent (alias)
start-agent

# Stop agent
stop-agent

# View logs
agent-logs

# Manual start
cd /home/vagrant/agent_b
./launch_offline.sh
```

## 🖥️ Windows Usage

Both Docker and Vagrant work perfectly on Windows:

1. **Install Docker Desktop** or **VirtualBox + Vagrant**
2. Open PowerShell or Command Prompt
3. Navigate to the project directory
4. Run the Docker or Vagrant commands above
5. Open Chrome/Edge to `http://localhost:7788`

The Linux browser runs inside the container/VM, so no Linux subsystem needed on Windows!

## 🔧 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs agent-b

# Increase shared memory
docker run --shm-size=4gb ...
```

### Can't access web UI
- Check firewall settings
- Ensure port 7788 is not in use
- Try `http://127.0.0.1:7788` instead of localhost

### Browser automation fails
- The browser runs inside the container
- Check container has enough memory (4GB recommended)
- Enable VNC to see what's happening

### API key errors
- Update the docker-compose.yml or pass via -e flags
- Ensure keys are valid and have credits

## 📊 Resource Requirements

- **CPU**: 2 cores minimum
- **RAM**: 4GB recommended, 2GB minimum
- **Disk**: 10GB free space
- **Network**: Internet connection for API calls

## 🔐 Security Notes

- API keys are passed as environment variables
- Use `.env` files for production
- The container runs Chrome with `--no-sandbox` for compatibility
- VNC is disabled by default for security

## 🚀 Production Deployment

For production, consider:
- Using Docker Swarm or Kubernetes
- Setting up proper logging
- Using secrets management
- Implementing monitoring
- Setting resource limits
- Using a reverse proxy (nginx)