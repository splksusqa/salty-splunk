# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  config.vm.box = "puphpet/ubuntu1404-x64"

  config.vm.define "linux" do |node|
    node.vm.box = "puphpet/ubuntu1404-x64"

    # states file
    node.vm.synced_folder "file_base", "/srv/salt/"
    node.vm.provision "file", source: "bash_profile", destination: ".bash_profile"

    node.vm.provision :salt do |salt|
      salt.minion_config = "config/minion"
      salt.install_master = false
      salt.bootstrap_options = "-P -F -c /tmp"
      salt.run_highstate = false
    end
  end

  config.vm.define "win" do |node|
    node.vm.box = "opentable/win-2012r2-standard-amd64-nocm"

    node.vm.provider "virtualbox" do |v|
      v.gui = true
    end

    node.vm.provider "vmware-fusion" do |v|
      v.gui = true
    end

    # node.vm.provision :salt do |salt|
    #   salt.minion_config = "config/minion"
    #   salt.install_master = false
    #   salt.bootstrap_options = "-P -F"
    #   salt.run_highstate = false
    # end

    node.vm.provision "shell", inline: <<-SHELL
      # iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
      # choco install saltminion -y
      # sudo apt-get update 
    SHELL
  end





  # config.vm.provision "shell", inline: <<-SHELL
  #   echo "test"
  #   # sudo apt-get update 
  # SHELL
end
