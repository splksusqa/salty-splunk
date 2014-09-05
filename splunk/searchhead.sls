include:
  - splunk.common

set-role:
  splunk:
    - configured
    - interface: rest
    - uri: services/search/distributed/peers
    - body:
        name: 'idx:port'
        remoteUsername: 'admin'
        remotePassword: 'changeme'
