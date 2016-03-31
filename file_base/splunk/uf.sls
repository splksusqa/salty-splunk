include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['universal-forwarder']['version'] }}
    - type: splunkforwarder
    - require:
      - sls: splunk.common



