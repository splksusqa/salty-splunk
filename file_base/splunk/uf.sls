include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - pkg_url: {{ pillar['universal-forwarder']['version'] }}
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
  {% if grains['os'] == 'Windows' %}
  win_firewall:
    - add_rule
    - localport: {{ pillar['universal-forwarder']['listening_ports'] }}
    - protocol: tcp
  {% endif %}
