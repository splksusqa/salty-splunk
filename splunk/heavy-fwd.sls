include:
  - splunk.common


set_fwd_server:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/data/outputs/tcp/server
    - body:
        name: 'host:port'
    - require:
      - splunk: install-splunk