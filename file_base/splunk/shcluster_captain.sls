include:
  - splunk.indexer
  - splunk.pip

bootstrap_captain:
  splunk:
    - shcluster_captain_bootstrapped
    - servers_list: '{{ salt["splunk.get_shc_member_list"]() }}'
  require:
    - sls: [splunk.indexer, splunk.pip]
