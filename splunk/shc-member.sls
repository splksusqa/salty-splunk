include:
 - splunk.common

{% set deployer = salt['publish.publish']('role:splunk-shc-deployer', 'splunk.get_mgmt_uri', None, 'grain') %}

set-shc:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        replication_port://{{ pillar['shc-replication']['port'] }}: {}
        shclustering:
          {% if deployer %}
          conf_deploy_fetch_url: {{ deployer.values()[0] }}
          {% endif %}
          disabled: '0'
          mgmt_uri: https://{{ grains['host']}}:{{ pillar['splunk']['splunkd_port'] }}
          pass4SymmKey: 'pass'
    - restart_splunk: True

{% set slaves = salt['publish.publish']('role:splunk-cluster-slave', 'splunk.get_mgmt_uri', None, 'grain') %}
{% set indexers = salt['publish.publish']('role:splunk-indexer', 'splunk.get_mgmt_uri', None, 'grain') %}
{% for recievers in [slaves, indexers] %}
  {% if recievers %}
    {% for host,uri in recievers.iteritems() %}

set_fwd_server_{{ host }}:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/data/outputs/tcp/server
    - body:
        name: {{ uri }}
    - require:
      - sls: splunk.common

    {% endfor %}
  {% endif %}
{% endfor %}

