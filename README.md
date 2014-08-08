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
- Installation in Ubuntu:
    1. sudo add-apt-repository ppa:saltstack/salt
    1. sudo apt-get update
    1. sudo apt-get install salt-master
    1. sudo apt-get install python-libcloud
    1. sudo apt-get install salt-cloud
    1. sudo apt-get install smbclient
    1. sudo dpkg -i data/winexe_1.00-1_amd64.deb (Note this .deb is in repo)

# Quickstart
1. Launch an EC2 ubuntu instance (will be running salt-master and salt-cloud)
1. Install salt-master and salt-cloud and their dependencies
1. Enable peer communications:

        peer:
          .*:
            - network.ip_addrs
            - splunk.splunkd_port

1. Clone this repo to your salt root (default is */srv/salt*):
    - `git clone https://susqa@bitbucket.org/splunksusqa/salt.git`
1. Copy pillar/* to your pillar_roots (or set salt pillar_roots to /srv/salt/pillar 
, default to */srv/pillar*):

        pillar_roots:
          base:
            - /srv/salt/pillar

1. Check the ip of the linux instance, set it in *cloud/cloud.profiles* (replace salt-master.qa)
1. Put your **AWS id** and **key** (for calling AWS API), **keyname** (ssh key pairs, only the name), 
   and **private_key** (the real ssh-key file that matches with keyname) to *cloud/cloud.providers*
1. Copy *cloud/cloud.profiles* and *cloud/cloud.providers* to */etc/salt/*. 
    - Check if you can list the provider: `salt-cloud --list-providers`
    - Check if you can access the ami: `salt-cloud --list-images aws_ec2`
    - Note: /srv/salt/ is the root for salt related stuff, if you changed the root, 
      remember to change win_installer path in cloud.profiles too.
1. Launch instances with salt-cloud:
    - `salt-cloud -p (win2012|win2008) <node1> <node2> <node3> ... -P`
    - Note: the node names need to contain **splunk-cluster-**(**master | searchhead | slave**)
1. Make sure the instances are running and connected to your salt master:
    - `salt  '*' test.ping`
    - Note: Windows need some time to start salt-minion service, but sometimes they're not started, 
      you can run the following command to start them:
        - `winexe -U Administrator%<passwd> //<ip> "sc start salt-minion"` 
1. Once all nodes are up and connected, run the command to setup the splunk cluster:
    - `salt '*' state.highstate`


# Documentation
- Saltstack official documentation: http://docs.saltstack.com

# Salt concepts and implementation for Splunk
## States
States (http://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html), 
or **sls** files, are used to define a desire state that we want a node to be in.
e.g., when a state defined as:

    apache:                              # name (will also be used as kwarg, **{"name": "apache"})
      pkg:                               # state module
        - installed                      # function of the above state module (pkg.py)
        - version: 2.2.15-29.el6.centos  # kwarg (**{"version": "2.2.15-29.el6.centos"})
      service:                           # state module
        - running                        # function (of service.py)
is called, salt will execute the "**pkg**" module's "**installed**" funciton 
(https://github.com/saltstack/salt/blob/develop/salt/states/pkg.py#L381) on the node.
Since the function "**installed**" has defined a parameter "**name**", the value "**apache**"
will be used as an arg for it, and there is another arg "**version**" will also be sent to 
"**installed**" function to perform corresponding executions, i.e., installing apache on 
the node.

Then, salt will execute "**running**" function of 2nd module "**service**"  
(https://github.com/saltstack/salt/blob/develop/salt/states/service.py#L261)
with **name=apache** as kwarg for it.


## Target nodes
Targeting minions is specifying which minions should run a command or execute a state.
e.g., when **top.sls** defined as 

    base:
      '*':
        - common
      'web1':
        - webserver

When state.highstate is called, all minions ('*') will execute the common.sls 
(or common/init.sls), and only minions' **id** match "web1" will execute webserver.sls
(webserver/init.sls)

There are several ways of targeting minions: 
(http://docs.saltstack.com/en/latest/topics/targeting/index.html#targeting)

- ID
- Grains (-G)
- Nodegroup(-N)
- IP/subnet (-S)
- Compound
    

## Modules
Salt execution modules (http://docs.saltstack.com/en/latest/ref/modules/), 
are used to perform certain **actions**, modules are also python scripts, 
but they cannot be called from state (sls) files, they're called from `salt` 
command, e.g.:

`salt '*' test.ping`

is calling function **ping** in **test** module, such action is used to see if 
minions are connected, they're also executed at minions.
But such actions are ad-hoc, non-stateful, and one-time command. 
Most common functions are **start**, **stop**, **restart/reload**, **status** 


## Pillar
Pillars (http://salt.readthedocs.org/en/latest/topics/pillar/) are purely **data**.
They're only available for targeted minions , so we can store sensitive data
in pillars. But pillar can be used as variables in states, e.g., if we have multiple 
roles, and we want to apply the same package but with different versions, we can 
define a default version, and other versions, then use them as variable in sls files.


## Implementations and implications.
1. States
    - Define desired splunk states
1. Modules
    - Actions
    - Tests
1. Pillar
    - only data


# Source structures & definitions

## _states

salt states modules
(http://docs.saltstack.com/en/latest/ref/states/writing.html)

## _modules

salt execution modules (http://docs.saltstack.com/en/latest/ref/modules/)

## pillar
salt pillar data.

## data
data that can be made available to minions, note that large datasets should be 
put at another data server instead of here.

## cloud
salt-cloud configurations, e.g., cloud.proviles and cloud.providers.

## splunk
Splunk states (sls) files.

## top.sls
The top state file for salt 
(http://docs.saltstack.com/en/latest/ref/states/top.html)

## README.md
This readme file.

# Resources
- Official github: https://github.com/saltstack/salt
- An overview (slides): http://www.slideshare.net/SaltStack/an-overvisaltstack-presentation-clean
- Beginners tutorial: https://blog.talpor.com/2014/07/saltstack-beginners-tutorial/
- CLI: http://docs.saltstack.com/en/latest/ref/cli/salt.html


# Known Issues
1. salt-cloud provisioning using winexe, which is incompatible with win2012R2
1. if you manually deleted the nodes (instead of using `salt-cloud -d <node>`), 
you will need to delete the keys as well:
`salt-key -d <node1> <node2> <node3> ...`
1. if you keep getting `SaltCloudSystemExit: Failed to authenticate against 
remote windows host`, 
try to increase the check interval (time.sleep) in 
*/usr/lib/python2.7/dist-packages/salt/utils/cloud.py* line308.
Because windows might be up but not yet be ready to install winexesvc, so it'll 
return an error, and salt-cloud would think there is an authentication error.
1. if you mange to use `cloud.map` to provision minions, you will encounter an
error (see the issue [here](https://github.com/saltstack/salt/issues/14593))
saying `The specified fingerprint in the master configuration file`. 
You'll need to edit 
[this line](https://github.com/saltstack/salt/blob/develop/salt/utils/__init__.py#L786)
with `key = ''.join(fp_.readlines()[1:-1]).replace("\r\n", "\n")`
to make windows minions provisioned by `salt-cloud -m cloud.map` happy

# Credits

