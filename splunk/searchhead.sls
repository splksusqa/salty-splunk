include:
  - splunk.common

add-peer:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/search/distributed/peers
    - body:
        name: 'idx:port'
        remoteUsername: 'admin'
        remotePassword: 'changeme'


