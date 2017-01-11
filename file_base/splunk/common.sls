
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

titanium:
  pip.installed:
  - name: titanium>=0.1.6
  - extra_index_url: "https://pypi.fury.io/m4dy9Unh83NCJdyGHkzY/beelit94/"