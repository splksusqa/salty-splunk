# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "puphpet/ubuntu1404-x64"

  # states file
  config.vm.synced_folder "file_base", "/srv/salt/"

  config.vm.provision :salt do |salt|
    salt.minion_config = "config/minion"
    salt.install_master = false
    salt.bootstrap_options = "-P -F -c /tmp"
    salt.run_highstate = false
  end


  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    echo "test"
    # sudo apt-get update 
  SHELL
end
