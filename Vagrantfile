# -*- mode: ruby -*-
# # vi: set ft=ruby :
#

Vagrant.configure("2") do |config|
    config.vm.box = "ubuntu/trusty64"
    config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    
    config.vm.provider :virutalbox do |vb|
        vb.customize [
            "modifyvm", :id,
            "--memory", "1024"
        ]
    end

    #Setup a private network and forward port 8080 to the host.
    config.vm.network "private_network", ip:"192.168.50.2"
    config.vm.network "forwarded_port", guest:8080, host:8080

    config.vm.provision "shell", path: "bootstrap.sh", privileged: false
end
