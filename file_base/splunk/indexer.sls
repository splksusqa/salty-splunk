install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}
