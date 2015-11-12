install-splunk:
  splunk:
    - installed
    - version: {{ salt['pillar.get']('version') }}