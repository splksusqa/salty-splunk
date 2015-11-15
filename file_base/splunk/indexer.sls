install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ salt['pillar.get']('version') }}