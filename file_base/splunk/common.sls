
# Linux
{% if grains['os'] != 'Windows' %}
python-pip:
  pkg:
    - installed

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
{% endif %}
