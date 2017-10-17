include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - pkg_url: {{ pillar['version'] }}
    {% set is_win_domain = salt.pillar.get('win_domain', default=false) %}
    {% if grains['os'] == 'Windows' and (is_win_domain != false) %}

    {% set domain = pillar['win_domain']['domain_name'] %}
    {% set user = pillar['win_domain']['username'] %}
    - LOGON_USERNAME: {{ domain }}\{{ user }}
    - LOGON_PASSWORD: {{ pillar['win_domain']['password'] }}
    {% endif %}
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

{% if pillar['server_name'] %}
set-server-name:
  splunk.configured:
    - conf_name: server
    - stanza_name: general
    - data:
        serverName: {{ pillar['server_name'] }}
{% endif %}

{% if grains['os'] == 'Windows' %}
  win_firewall:
    - add_rule
    - localport: {{ pillar['listening_ports'] }}
    - protocol: tcp
{% endif %}

update-mine-date:
  module.run:
    - name: mine.update
    - require:
      - splunk: install-splunk
