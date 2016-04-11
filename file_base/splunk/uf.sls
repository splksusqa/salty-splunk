include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['universal-forwarder']['version'] }}
    - type: splunkforwarder
    - require:
      - sls: splunk.common

add-forward-server:
  splunk:
    - forward_servers_added
    - servers: {{ pillar['universal-forwarder']['forward-servers'] }}
