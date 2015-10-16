include:
 - splunk.common

set-shc-deployer:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        shclustering:
          pass4SymmKey: 'pass'
    - restart_splunk: True

