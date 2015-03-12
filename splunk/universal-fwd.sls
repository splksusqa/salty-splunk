include:
  - splunk.common

{% set slaves = salt['publish.publish']('role:splunk-cluster-slave', 'splunk.get_listening_uri', 'type=splunktcp', 'grain') %}
{% set indexers = salt['publish.publish']('role:splunk-indexer', 'splunk.get_listening_uri', 'type=splunktcp', 'grain') %}

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


data:
  splunk:
    - data_monitored
    - source: {{ pillar['dataset']['1m'] }}
    - require:
      - sls: splunk.common


app:
  splunk:
    - app_installed
    - source: {{ pillar['app']['gendata'] }}
    - require:
      - sls: splunk.common

# uf doesnt have such rest endpoint
#app:
#  splunk:
#    - configured
#    - interface: rest
#    - method: post
#    - uri: services/apps/appinstall
#    - body:
#        name: {{ pillar['app']['gendata'] }}
#    - require:
#      - sls: splunk.common