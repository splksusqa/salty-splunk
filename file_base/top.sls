# Using 'id' for now, but better way of specifying nodes is by its 'role'

base:

  'role:indexer':
    - match: grain
    - splunk.indexer
