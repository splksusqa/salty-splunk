install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}

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