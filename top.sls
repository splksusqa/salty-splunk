# Using 'id' for now, but better way of specifying nodes is by its 'role'

base:

  'role:splunk-cluster-master':
    - match: grain
    - splunk.cluster-master

  'role:splunk-cluster-searchhead':
    - match: grain
    - splunk.cluster-searchhead

  'role:splunk-cluster-slave':
    - match: grain
    - splunk.cluster-slave

  'role:splunk-shc-captain':
    - match: grain
    - splunk.shc-captain

  'role:splunk-shc-member':
    - match: grain
    - splunk.shc-member

  'role:splunk-shc-deployer':
    - match: grain
    - splunk.shc-deployer

  'role:splunk-indexer':
    - match: grain
    - splunk.indexer

  'role:splunk-searchhead':
    - match: grain
    - splunk.searchhead

  'role:splunk-universal-fwd':
    - match: grain
    - splunk.universal-fwd

  'role:splunk-heavy-fwd':
    - match: grain
    - splunk.heavy-fwd

  'role:splunk-light-fwd':
    - match: grain
    - splunk.light-fwd

  'role:splunk-dmc':
    - match: grain
    - splunk.dmc

  'role:splunk-lic-master':
    - match: grain
    - splunk.lic-master

  'role:splunk-deployment-server':
    - match: grain
    - splunk.deployment-server

  'role:splunk-ember-indexer':
    - match: grain
    - splunk.ember-indexer

  'role:splunk-ember-heavy-fwd':
    - match: grain
    - splunk.ember-heavy-fwd

  'role:splunk-ember-shc-deployer':
    - match: grain
    - splunk.ember-shc-deployer

  'role:splunk-ember-shc-captain':
    - match: grain
    - splunk.ember-shc-captain

  'role:splunk-ember-shc-member':
    - match: grain
    - splunk.ember-shc-member

  'role:splunk-ember-searchhead':
    - match: grain
    - splunk.ember-searchhead
