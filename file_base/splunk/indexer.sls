include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}
    {% if (grains['os'] == 'Windows' and pillar['win_domain']['domain_name'] != 'NaN') %}
    - LOGON_USERNAME: {{ pillar['win_domain']['domain_name'] }}\{{ pillar['win_domain']['username'] }}
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

update-mine-date:
  module.run:
    - name: mine.update
    - require:
      - splunk: install-splunk
