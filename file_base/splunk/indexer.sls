include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}
    - require:
      - sls: splunk.common

allow_remote_login:
  splunk.configured:
    - conf_name: server
    - stanza_name: general
    - data:
      allowRemoteLogin: always

enable-listening-port:
  splunk:
    - listening_ports_enabled
    - ports: {{ pillar['listening_ports'] }}
