include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['universal-forwarder']['version'] }}
    - type: splunkforwarder
    - require:
      - sls: splunk.common

sleep_after_install_splunk:
  module.run:
    - name: test.sleep
    - length: 30
    - onchanges:
      - splunk: install-splunk

allow_remote_login:
  module.run:
    - name: splunk.allow_remote_login
    - onchanges:
      - module: sleep_after_install_splunk

add-forward-server:
  splunk:
    - forward_servers_added

enable-listening-port:
  splunk:
    - listening_ports_enabled
    - ports: {{ pillar['universal-forwarder']['listening_ports'] }}
