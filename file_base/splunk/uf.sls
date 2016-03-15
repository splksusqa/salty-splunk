include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}
    - type: splunkforwarder
    - require:
      - sls: splunk.pip

allow_remote_login:
  module.run:
    - name: splunk.allow_remote_login
    - require:
      - splunk: install-splunk

