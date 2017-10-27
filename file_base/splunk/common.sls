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

install-requests:
  pip.installed:
    - name: requests
    - cwd: 'C:\salt\bin\scripts'
    - bin_env: 'C:\salt\bin\scripts\pip.exe'

install-splunk-sdk:
  pip.installed:
    - name: splunk-sdk
    - cwd: 'C:\salt\bin\scripts'
    - bin_env: 'C:\salt\bin\scripts\pip.exe'

{% endif %}
