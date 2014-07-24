# About

This is a Splunk internal project that uses saltstack (http://www.saltstack.com/) 
to do provisioning, orchestration, and testing. This project amis to minimize the 
efforts to setup, control, and run tests over arbitrary deployments. By utilizing 
salt's remote execution ability, we can write python scripts that's like running it 
locally,  without worrying about ssh and quotes that introduced by underlaying shell. 
Hence, the framework also minimizes the efforts to write testing scripts for complex 
Splunk deployments.


# Prerequisites
- Python 2.7.x
- salt-master (requires: http://docs.saltstack.com/en/latest/topics/installation/)
- salt-cloud (requires: python-libcloud, smbclient, winexe)


# Quickstart
1. Launch an EC2 linux instance (will be running salt-master and salt-cloud)
1. Install salt-master and salt-cloud and their dependencies.
1. Clone this repo to your salt root (default is */srv/salt*):
    - ````git clone https://susqa@bitbucket.org/splunksusqa/salt.git````
1. Check the ip of the linux instance, set it in *cloud/cloud.profiles* (replace salt-master.qa)
1. Put your **AWS id** and **key** (for calling AWS API), **keyname** (ssh key pairs, only the name), 
   and **private_key** (the real ssh-key file that matches with keyname) to *cloud/cloud.providers*
1. Copy *cloud/cloud.profiles* and *cloud/cloud.providers* to */etc/salt/*. 
    - Check if you can list the provider: ````salt-cloud --list-providers````
    - Check if you can access the ami: ````salt-cloud --list-images aws_ec2````
    - Note: /srv/salt/ is the root for salt related stuff, if you changed the root, 
      remember to change win_installer path in cloud.profiles too.
1. Launch instances with salt-cloud:
    - ````salt-cloud -p (win2012|win2008) <node1> <node2> <node3> ... -P````
    - Note: the node names need contain **splunk-cluster-**(**master | searchhead | slave**)
1. Make sure the instances are running and connected to your salt master:
    - ````salt  '*' test.ping````
    - Note: Windows need some time to start salt-minion service, but sometimes they're not started, 
      you can run ````winexe -U Administrator%<passwd> //<ip> "sc start salt-minion"```` to start them.
1. Once all nodes are up and connected, run the command to setup the splunk cluster:
    - ````salt '*' state.highstate````


# Documentation
- Saltstack official documentation: http://docs.saltstack.com


# Source structures
- _modules
- _states
- cloud
- data
- pillar
- splunk


# Resources
- https://github.com/saltstack/salt
- https://github.com/techhat/salt/
- http://www.slideshare.net/SaltStack/an-overvisaltstack-presentation-clean
- https://blog.talpor.com/2014/07/saltstack-beginners-tutorial/


# Credits