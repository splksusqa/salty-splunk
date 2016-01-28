include:
  - splunk.pip

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}
    - require:
      - sls: splunk.pip

allow_remote_login:
  module.run:
    - name: splunk.allow_remote_login
    - require:
      - splunk: install-splunk

{% if grains['os'] == 'Windows' %}
SplunkWebPort:
  win_firewall:
    - add_rule
    - localport: 8000
    - protocol: tcp

SplunkdPort:
  win_firewall:
    - add_rule
    - localport: 8089
    - protocol: tcp
{% endif %}