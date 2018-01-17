include:
  - splunk.indexer

add_license:
  splunk:
    - license_added
    - license_name: {{ pillar['license_name'] }}
  require:
    - sls: splunk.indexer
