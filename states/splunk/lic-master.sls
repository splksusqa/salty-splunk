include:
  - splunk.common

/opt/splunk/splunk.lic:
  file.managed:
    - source: salt://data/splunk.lic
    - user: root
    - group: root
    - mode: 644

set-lic:
  splunk:
    - configured
    - interface: rest
    - uri: services/licenser/licenses
    - method: post
    - body:
        name: /opt/splunk/splunk.lic
    - require:
      - sls: splunk.common

set-lic-group:
  splunk:
    - configured
    - interface: rest
    - uri: services/licenser/groups/Enterprise
    - method: post
    - body:
         is_active: 1

restart-splunk:
  splunk:
    - cli_configured
    - command: restart

