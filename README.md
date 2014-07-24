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


# Features


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