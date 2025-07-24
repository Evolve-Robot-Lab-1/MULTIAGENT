# Windows Setup Guide for DocAI + AGENT_B

This guide will help you run the DocAI + AGENT_B project on Windows using Vagrant.

## Prerequisites

1. **Install VirtualBox** (6.1 or newer)
   - Download from: https://www.virtualbox.org/wiki/Downloads
   - Choose "Windows hosts" version
   - Run installer with default settings

2. **Install Vagrant** (2.2.19 or newer)
   - Download from: https://www.vagrantup.com/downloads
   - Choose Windows 64-bit version
   - Restart your computer after installation

3. **Enable Virtualization** in BIOS
   - Restart computer and enter BIOS (usually F2, F10, or Del key)
   - Enable "Intel VT-x" or "AMD-V" virtualization
   - Save and exit

## Setup Instructions

### 1. Prepare the Project

1. Copy the entire `docai_final` folder to your Windows machine
2. Place it in a path without spaces (e.g., `C:\projects\docai_final`)
3. Open Command Prompt or PowerShell as Administrator
4. Navigate to the project folder:
   ```cmd
   cd C:\projects\docai_final
   ```

### 2. Start the Vagrant VM

```cmd
# First time setup (this will take 10-20 minutes)
vagrant up

# If you see any errors, try:
vagrant provision
```

### 3. Access the VM

```cmd
# Connect to the VM
vagrant ssh
```

### 4. Run the Services

Once inside the VM:

```bash
# Option 1: Run AGENT_B only
cd /home/vagrant/docai_final
./start_agent_b.sh

# Option 2: Run DocAI only
cd /home/vagrant/docai_final
./start_docai.sh

# Option 3: Run everything
cd /home/vagrant/docai_final
./start_all.sh
```

### 5. Access from Windows Browser

- **AGENT_B**: http://localhost:7788
- **DocAI**: http://localhost:8090
- **Gradio**: http://localhost:7860

## Common Commands

### VM Management
```cmd
# Start VM
vagrant up

# Stop VM
vagrant halt

# Restart VM
vagrant reload

# SSH into VM
vagrant ssh

# Destroy VM (if you want to start fresh)
vagrant destroy
```

### Inside the VM
```bash
# Check if services are running
ps aux | grep python

# Check logs
tail -f agent_b.log

# Restart a service
pkill -f webui.py
./start_agent_b.sh
```

## Troubleshooting

### 1. "VT-x is not available" error
- Enable virtualization in BIOS
- Disable Hyper-V: `bcdedit /set hypervisorlaunchtype off`
- Restart computer

### 2. Port already in use
- Change port in Vagrantfile
- Or kill the process using the port

### 3. Vagrant ssh fails
- Use PuTTY or Git Bash instead
- Or try: `vagrant ssh-config` to get connection details

### 4. Slow performance
- Increase RAM in Vagrantfile (change `vb.memory = "4096"` to `"8192"`)
- Ensure Windows Defender isn't scanning the VM folder

### 5. File sync issues
- Try: `vagrant reload`
- Check Windows Firewall settings

## Advanced Configuration

### Change VM Resources
Edit `Vagrantfile`:
```ruby
vb.memory = "8192"  # 8GB RAM
vb.cpus = 4         # 4 CPU cores
```

### Use Different Ports
Edit `Vagrantfile`:
```ruby
config.vm.network "forwarded_port", guest: 7788, host: 8888
```

### Enable GUI Mode (for debugging)
Edit `Vagrantfile`:
```ruby
vb.gui = true
```

## Notes

- First startup will download Ubuntu image (~500MB)
- Provisioning installs all dependencies (~15-20 minutes)
- The VM uses about 10GB disk space
- All project files are synced between Windows and VM
- Changes made in Windows are immediately available in VM

## Support

If you encounter issues:
1. Check the Vagrant output for errors
2. Look at logs inside the VM
3. Ensure all prerequisites are properly installed
4. Try destroying and recreating the VM: `vagrant destroy && vagrant up`