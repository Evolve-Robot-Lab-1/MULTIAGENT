# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Use Ubuntu 22.04 LTS
  config.vm.box = "ubuntu/jammy64"
  
  # VM configuration
  config.vm.provider "virtualbox" do |vb|
    vb.name = "docai-agent-b"
    vb.memory = "4096"
    vb.cpus = 2
    # Enable GUI if needed for debugging
    vb.gui = false
    # Enable shared clipboard
    vb.customize ["modifyvm", :id, "--clipboard", "bidirectional"]
    # Enable drag and drop
    vb.customize ["modifyvm", :id, "--draganddrop", "bidirectional"]
  end
  
  # Network configuration
  # Forward ports for web interfaces
  config.vm.network "forwarded_port", guest: 7788, host: 7788  # AGENT_B
  config.vm.network "forwarded_port", guest: 7860, host: 7860  # Gradio default
  config.vm.network "forwarded_port", guest: 8090, host: 8090  # DocAI
  
  # Sync the entire project folder
  config.vm.synced_folder ".", "/home/vagrant/docai_final", type: "virtualbox"
  
  # Provision the VM
  config.vm.provision "shell", path: "vagrant_provision.sh"
  
  # Run startup script on every boot
  config.vm.provision "shell", run: "always", inline: <<-SHELL
    echo "Starting services..."
    # Ensure LibreOffice is available
    sudo systemctl start libreoffice || true
  SHELL
  
  # Post-up message
  config.vm.post_up_message = <<-MSG
    ========================================
    DocAI + AGENT_B Vagrant Box is ready!
    
    To access the VM:
      vagrant ssh
    
    To run AGENT_B:
      vagrant ssh
      cd /home/vagrant/docai_final
      source turboo_linux_new/bin/activate
      cd AGENT_B
      python webui.py --ip 0.0.0.0 --port 7788
    
    Access from Windows browser:
      AGENT_B: http://localhost:7788
      DocAI: http://localhost:8090
    
    To stop the VM:
      vagrant halt
    ========================================
  MSG
end