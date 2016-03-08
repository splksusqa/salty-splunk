# About

This is a Splunk internal project that utilize saltstack 
(http://www.saltstack.com/)  to do provisioning, orchestration, and testing. 
This project aims to minimize the efforts to setup, control, and run tests over 
arbitrary deployments. Salt's remote execution capability also minimizes the 
efforts to write required modules, since there is no ssh or underlying 
transportation layer libraries involved in the python modules, all the modules 
are executed remotely.

# List of roles

search-head
indexer
indexer-cluster-master
indexer-cluster-peer
indexer-cluster-search-head
search-head-cluster-member
search-head-cluster-deployer
search-head-cluster-first-captain (run time generated)
distributed-management-console (not implemented)
central-license-master
central-license-slave
deployment-server
deployment-client
multi-site-#-member (not implemented)
multi-site-master (not implemented)
universal-forwarder
