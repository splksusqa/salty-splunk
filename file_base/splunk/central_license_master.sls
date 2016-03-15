include:
  - splunk.indexer

add_license:
  splunk:
    - license_added
    - license_path: {{ pillar['license_path'] }}
  require:
    - sls: splunk.indexer