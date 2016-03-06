# About

This is a Splunk internal project that utilize saltstack 
(http://www.saltstack.com/)  to do provisioning, orchestration, and testing. 
This project aims to minimize the efforts to setup, control, and run tests over 
arbitrary deployments. Salt's remote execution capability also minimizes the 
efforts to write required modules, since there is no ssh or underlying 
transportation layer libraries involved in the python modules, all the modules 
are executed remotely.

