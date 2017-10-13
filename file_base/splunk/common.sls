# Linux
{% if grains['os'] != 'Windows' %}
python-pip:
  pkg.installed

requests:
  pip.installed:
    - require:
      - pkg: python-pip

splunk-sdk:
  pip.installed:
    - require:
      - pkg: python-pip
# Windows
{% else %}
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

requests:
  pip.installed

splunk-sdk:
  pip.installed

{% endif %}
