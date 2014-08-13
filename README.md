# About

This is a Splunk internal project that utilize saltstack 
(http://www.saltstack.com/)  to do provisioning, orchestration, and testing. 
This project aims to minimize the efforts to setup, control, and run tests over 
arbitrary deployments. Salt's remote execution capability also minimizes the 
efforts to required modules, since there is no ssh or underlying transportation
layer libraries involved in the python modules, modules are executed remotely.


# Prerequisites
- Python 2.7.x
- salt-master (http://docs.saltstack.com/en/latest/topics/installation/)
- salt-cloud (requires: python-libcloud, smbclient, winexe)


# Steps
## Quickstart script to install & setup a salt-master
1. Save the following texts into a script (e.g. setup-salt-master.sh),
   - if you need to launch salt-minions with salt-cloud on ec2, replace **<access key id>** and **<secret access key>** in the script   
     with your AWS access key id and secret access key.
   - If you're using EC2 as your master, you can paste the following
     texts into **user data** section in the page after selecting desired ami
   - **NOTE**: this is script is only tested in Ubuntu and Centos6, and you'll
     hit an issue (see *Known issues* section) on Redhat 7 of EC2.
   
        #! /bin/bash
        # you can check /var/log/cloud-init-output.log for the outputs
        # usually the whole shell script takes around 70s
        ACCESS_KEY_ID="<access key id>"
        SECRET_ACCESS_KEY="<secret access key>"
        is_ubuntu=`grep 'Ubuntu' /proc/version`
        is_redhat=`grep 'Red Hat' /proc/version` #also for centos 6
        if [ "$is_ubuntu" ]; then
            sudo add-apt-repository ppa:saltstack/salt -y
            sudo apt-get update -y 
            sudo apt-get install salt-master -y
            sudo apt-get install python-libcloud -y 
            sudo apt-get install salt-cloud -y
            sudo apt-get install smbclient -y
            wget http://download.opensuse.org/repositories/home:/uibmz:/opsi:/opsi40-testing/xUbuntu_12.04/amd64/winexe_1.00.1-1_amd64.deb
            sudo dpkg -i winexe_1.00.1-1_amd64.deb
        elif [ "$is_redhat" ]; then
            # The steps are for redhat 6
            sudo rpm -Uvh http://ftp.linux.ncsu.edu/pub/epel/6/i386/epel-release-6-8.noarch.rpm
            sudo yum -y install salt-master
            sudo yum -y install samba-client
            sudo yum -y install python-libcloud
            sudo yum -y install salt-cloud
            curl -O curl -O http://ftp5.gwdg.de/pub/opensuse/repositories/home:/uibmz:/opsi:/opsi40-testing/CentOS_CentOS-6/x86_64/winexe-1.00.1-10.2.x86_64.rpm
            sudo rpm -Uvh winexe-1.00.1-10.2.x86_64.rpm 
            sudo chkconfig salt-master on
        fi
        echo -e "\npeer:\n  .*:\n    - network.ip_addrs\n    - splunk.splunkd_port\n" | sudo tee -a /etc/salt/master > /dev/null
        echo -e "\npillar_roots:\n  base:\n    - /srv/salt/pillar\n" | sudo tee -a /etc/salt/master > /dev/null
        echo -e "\nfile_recv: True\n" | sudo tee -a /etc/salt/master > /dev/null
        echo """-----BEGIN RSA PRIVATE KEY-----
        MIIEogIBAAKCAQEAqhjhYPZcF4WwWyPLTFssLnovuF84B0qfNONrXCOnTnS0YOO7
        NYPAcwYsnqfW849Hq28tkslbEELltWv3f1INkwyo0ZwE6WhNwfgcyNy49y5Cu6P6
        +RSL0msRhF3fipiQKmY8vwO/zrZQ4Y/lj6smFalTMcT7stZXAdzHEQNY5S1Vfo4Z
        0CbXD6rGUc/Jo6+2rje/iUHm8Z+EH5xkIXzX5PUab3VtSNZdHGOFjdtXSsfMDrdd
        VDwk6rU/Hb3XEGMVomnm+4PyANHs0El8W1WRdk9f2H+0W6YkVDOEPHd3uUvmyt88
        D22huFYDkw4OTQN5KoTSiVZe3il5TTDP7lASTwIDAQABAoIBAFehN8M/SFRp8GAT
        wbGVqt5K3njKvU+sVvblTrMKPzBBGYhs6k54kNXxUV1vNGMH5rFgNodPqtVm0Xa0
        p631NL8UH4jVKwagUKbkTtgANl5Je+G1ah+WQS5nMIAT6I07adIeF5+Eq/Uvod2C
        x45LavRv5kdWpyEMIYj5F6khI1P1Pr+QjNgpI5UiAik+GW7UydgkSGPpuVL5jDIH
        Mv5yTvvMDct/KDnLsjwRhvZ4b0fIDu49eMxuKw6JYETMsI2EAzIqxJRNgz2TFsKo
        HSOP0p5Xpyhc0ty47Fzsb5xX0A6v6gCzAjAtNei29N3N8epcqboPIGV8oeQrRUZw
        blmIShkCgYEA2pGUFL4/vUa+b4N+jqirzmASO3Ayyyt8bfKBpaCHRt3E7pxyhXnl
        GREsh2cAdIfnAIXBYQJlzphZCVwiXQmLII6IPANLKV3KHvB6GivCMOdW4yfmRw5x
        7gCx5UYt9EWqDNdxbyUBIhgoedvtVXACRMVWnceP2t7cEYcSErHLpgUCgYEAxzo6
        5eyXLZKPvBKfu2bg/lriP+ycZQVb5EPuglGDxMTGWy++KMIm2XRA9KTFSxtSmXWf
        gIRnVEL3BMAyhTGgQpzPVfq++mYJR7sTMXrWaR4bSS7zSF09+E3vVQ809HYoR5nY
        KGERbWQTBLOUrBeqD5+UiGo87MsTElbSfllwU0MCgYBF7d3a5SOvgzraos+TBRQy
        6znqGnOl3TvqUXR5cWrWmY2wag2Z9u39nykICUR0BCc8W48LYqEAAG48OGYmLi99
        Mx0TVlpt2bwZOgdW6DkxPFLoSpO6mDyLUV2ZZWK+jKtjgGqijMxYBDKvClZcx4Fy
        T1DvGjJEbJksYnK92HS3oQKBgAPmdO65YgBHZT72UmA11GPGXbWIqUsk/raKSeoN
        NHouq/9vANcFbgNFzlu7ug0NXOGaNuQqM2en4/QY2yRWY1/KeBijzwdR5g6cb/TB
        Bd+K8lfNbn/VK3hn9i6BHLVIduNn9J5dwByXH/Qwm9F+qRqjMiI1ijnMg/QQ9Q/6
        KkPHAoGAe5oKcQKcbz1ipOZKB3V+nZSOK/gTxvAsRjj5uGcmCPIMvh4/Q6e828Ss
        00R+TTSu4s3zU0AdR8FfeBDt7QUZYyRi4Ffdj0LxwyrSaM5zRN1UeHGvFmZata9Q
        uQ9uXqcY8tDDphSDttld3FwtLd1vH64jL/FASKjZX67EkzPeKvM=
        -----END RSA PRIVATE KEY-----""" | sudo tee /root/.ssh/id_rsa_bitbucket > /dev/null
        echo -e "Host bitbucket.org\n\tHostName bitbucket.org\n\tUser git\n\tIdentityFile ~/.ssh/id_rsa_bitbucket\n\tStrictHostKeyChecking no\n" | sudo tee -a /root/.ssh/config > /dev/null
        sudo chmod 400 /root/.ssh/id_rsa_bitbucket
        sudo git clone git@bitbucket.org:splunksusqa/salt.git /srv/salt
        sudo sed -i "s/salt-master.qa/`hostname -I`/" /srv/salt/cloud/cloud.profiles 
        sudo sed -i "/^  id/ s/:.*/: $ACCESS_KEY_ID/" /srv/salt/cloud/cloud.providers
        sudo sed -i "/^  key:/ s/:.*/: $SECRET_ACCESS_KEY/" /srv/salt/cloud/cloud.providers 
        sudo cp /srv/salt/cloud/* /etc/salt/
        sudo service salt-master restart

## Steps to install & step a salt-master
1. Launch an EC2 ubuntu instance (will be running salt-master and salt-cloud).
1. Install salt-master and salt-cloud and their dependencies.
1. Clone this repo to your salt root (default is */srv/salt*, so you can run the 
   following command in */srv/*):
    - `git clone https://susqa@bitbucket.org/splunksusqa/salt.git`
1. Install winexe from repo:
    - `sudo dpkg -i data/winexe_1.00.1-1_amd64.deb`
1. Enable peer communications (edit **/etc/salt/master**):

        peer:
          .*:
            - network.ip_addrs
            - splunk.splunkd_port

1. Copy pillar/* to your pillar_roots (default is */srv/pillar*) or set salt 
   pillar_roots to */srv/salt/pillar* (edit **/etc/salt/master**), i.e.:

        pillar_roots:
          base:
            - /srv/salt/pillar

1. (Optional)You'll need to set `file_recv: True` (in **/etc/salt/master**)
   to enable retrieving files from minions, e.g.:
    - `salt '*' cp.push <file path in minion>`
1. Check the IP of the salt-master, set it in *cloud/cloud.profiles* 
   (replace **salt-master.qa** with the real IP)
1. Put the followings to *cloud/cloud.providers*
    - **AWS id** (Access key ID)
    - **key** (Secret access key)
    - **keyname** (ssh key pairs, only the name)
    - **private_key** (the real ssh-key file that matches with keyname)
1. Copy *cloud/cloud.profiles* and *cloud/cloud.providers* to */etc/salt/*. 
    - Check if you can access the ami: `salt-cloud --list-images aws_ec2`
    - Note: */srv/salt/* is the root for salt related stuff, if you changed the 
      root, remember to change **win_installer** path in *cloud.profiles* too.

## Launch instances with salt-cloud
1. The command:
    - `salt-cloud -p <profile> <node1> <node2> <node3> ... -P`
        - You can check `cloud.profiles` for available profiles.
1. Make sure the instances are running and connected to your salt master:
    - `salt  '*' test.ping`
    - Note: Windows need some time to start salt-minion service, but sometimes 
      they're not started, you can run the following command to start them:
        - `winexe -U Administrator%<passwd> //<ip> "sc start salt-minion"` 
1. Once all nodes are connected, run the command to setup the splunk:
    - `salt '*' state.highstate`


# Documentation
- Saltstack official documentation: http://docs.saltstack.com
- Project documentation: TBD (will use Sphinx: http://sphinx-doc.org/)

# Bacic Salt concepts 
## States
States 
(http://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html), 
or **sls** files, are used to define a desire state that we want a node to be 
in, e.g., when a state defined as:

    apache:                # name (can be used as kwarg, **{"name": "apache"})
      pkg:                 # state module
        - installed        # function of the above state module (pkg.py)
        - version: 2.2.15  # kwarg (**{"version": "2.2.15"})
      service:             # state module
        - running          # function (of service.py)
is called, salt will execute the "**pkg**" module's "**installed**" funciton 
(https://github.com/saltstack/salt/blob/develop/salt/states/pkg.py#L381) on the 
node. Since the function "**installed**" has defined a parameter "**name**", the
 value "**apache**" will be used as an arg for it, and there is another arg 
 "**version**" will also be sent to  "**installed**" function to perform 
corresponding executions, i.e., install apache on the node.

Then, salt will execute "**running**" function of 2nd module "**service**"  
(https://github.com/saltstack/salt/blob/develop/salt/states/service.py#L261)
with **name=apache** as kwarg for it.

So actually the above .sls file defined two states, one is making sure the 
apache pkg is installed at version 2.2.15, and another is making sure apache 
service is running. The real worker to make things happen are **state modules**
(will be discussed in later section.)


## Target nodes
Targeting minions is specifying which minions should run a command or execute a 
state. e.g., when **top.sls** defined as 

    base:
      '*':
        - common
      'web1':
        - webserver
      'role:db':
        - match: grains
        - dbserver

When state.highstate is called, all minions ('*') will execute the common.sls 
(or common/init.sls), and only minions' **id** match "web1" will execute 
webserver.sls (webserver/init.sls). The 3rd one, **role:db** uses **grains** to
match minions (specified by **- match: grains**), so only the minions that have 
**role=db** key-value in their **grains** will execute dbserver.sls.

There are several ways of targeting minions: 
(http://docs.saltstack.com/en/latest/topics/targeting/index.html#targeting)

| Targets   | Usage in cli commands                                             | Used in sls files                                                 |
|-----------|-------------------------------------------------------------------|-------------------------------------------------------------------|
| ID        | `salt '*' test.ping`                                              | `'*'`                                                             |
|           | `salt -E 'prod-.*' test.ping`                                     | `'prod-.*'` (match: pcre)                                         |
|           | `salt -L 'web1,web2' test.ping`                                   | `'web1, web2'` (match: list)                                      |
| Grains    | `salt -G 'os:Windows' test.ping`                                  | `'os:Windows'` (match: grain)                                     |
|           | `salt --grain-pcre 'role:web-.*' test.ping`                       | `'role:web-.*'` (match: grain_pcre)                               |
| Pillar    | `salt -I 'master:ssh_user:root' test.ping`                        | `'master:ssh_user:root'` (match: pillar)                          |
| IP/Subnet | `salt -S '172.18.90.221' test.ping`                               | `'172.18.90.221'` (match: ipcidr)                                 |
| Compound  | `salt -C 'webserv* and G@os:Debian or E@web-dc1-srv.*' test.ping` | `'webserv* and G@os:Debian or E@web-dc1-srv.*'` (match: compound) |
| Nodegroup | `salt -N 'group1' test.ping`                                      | nodegroups: (defined in **/etc/salt/master**)                     |
|           |                                                                   |     group1: 'L@foo.domain.com,bar.domain.com'                     |


## Modules
There are two types of modules: **State modules** 
(http://docs.saltstack.com/en/latest/ref/states/writing.html)
and **Execution modules** 
(http://docs.saltstack.com/en/latest/ref/modules/)

### State modules
Salt state modules are the real actual enforcement and management of the states
that defined in the **.sls** files. These modules are written in python, used to 
realize the defined states (in .sls files) that we want. State modules should 
check the current states within a node and make necessary changes if the state
is not met the defined states. Take the apache example in *State* section,
the pkg is state module, and the **installed** function will be executed with  
**\*\*{name=apache, version=2.2.15}** as kwargs to check if apache 2.2.15 is
installed. If it's installed with 2.2.15, then function will do nothing,
if it's not installed, the function will try to install apache 2.1.5 on the 
node. Then the **running** function in **service** module will check if apache 
is running. 

The full list of builtin state modules is at:
http://docs.saltstack.com/en/latest/ref/states/all/ and source:
https://github.com/saltstack/salt/tree/2014.1/salt/modules

### Execution modules
Salt execution modules are used to perform certain **actions**, modules are 
also written in python, but they cannot be called from state (sls) files, 
they're called from `salt` cli command, e.g.:

`salt '*' test.ping`

is calling function **ping** in **test** module, such action is used to see if 
minions are connected, they're also executed at minions.
But such actions are ad-hoc, non-stateful, and one-time command. 
Most common functions are **start**, **stop**, **restart/reload**, **status** 

The full list of builtin execution modules is at:
http://docs.saltstack.com/en/latest/ref/modules/all/, and source:
https://github.com/saltstack/salt/tree/2014.1/salt/states

## Pillar
Pillars (http://salt.readthedocs.org/en/latest/topics/pillar/) are purely 
**data**. They're available for targeted minions only, so we can store sensitive
 data in pillars. But pillar can also be used as variables in states, e.g., if 
we have multiple roles, and we want to apply the same package but with different
versions, we can define a default version, and other versions, then use them as 
variable in sls files.


# Source structures & definitions

## _states
splunk states modules

## _modules
splunk execution modules

## pillar
 pillar data.

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
1. When trying to install salt-master, you'll hit an issue on RedHat 7 of EC2:

        Error: Package: salt-2014.1.7-3.el6.noarch (epel)
               Requires: python(abi) = 2.6
               Installed: python-2.7.5-16.el7.x86_64 (@anaconda/7.0)
                   python(abi) = 2.7
                   python(abi) = 2.7

1. salt-cloud provisioning using winexe, which is incompatible with win2012R2
    - might be compatible with win2012R2 with winexe_1.00.1-1_amd64.deb, but not
      fully tested yet.
1. if you manually deleted the nodes (instead of using `salt-cloud -d <node>`), 
you will need to delete the keys as well:
`salt-key -d <node1> <node2> <node3> ...`
1. if you keep getting `SaltCloudSystemExit: Failed to authenticate against 
remote windows host`, 
try to increase the check interval (time.sleep) in 
*/usr/lib/python2.7/dist-packages/salt/utils/cloud.py* line308.
Because windows might be up but not yet be ready to install winexesvc, so it'll 
return an error, and salt-cloud would think there is an authentication error.
1. if you manage to use `cloud.map` to provision minions, you will encounter an
error (see the issue [here](https://github.com/saltstack/salt/issues/14593))
saying `The specified fingerprint in the master configuration file`. 
You'll need to edit 
[this line](https://github.com/saltstack/salt/blob/develop/salt/utils/__init__.py#L786)
with `key = ''.join(fp_.readlines()[1:-1]).replace("\r\n", "\n")`
to make windows minions provisioned by `salt-cloud -m cloud.map` happy

# Credits

