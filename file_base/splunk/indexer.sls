include:
  - splunk.pip

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}

allow-remote-login:
  splunk:
    - remote_login_allowed
    - require:
      - sls: splunk.pip

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