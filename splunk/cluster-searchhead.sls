include:
  - splunk.common

#set-searchhead:
#  splunk:
#    - configured
#    - interface: rest
#    - method: post
#    - uri: services/cluster/config/config
#    - body:
#        mode: searchhead
#        master_uri: "{{ salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain').values()[0] }}"
#    - require:
#      - sls: splunk.common

{% set master = salt['publish.publish']('role:splunk-cluster-master', 'splunk.get_mgmt_uri', None, 'grain') %}

set-searchhead:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        clustering:
          mode: searchhead
          master_uri: "{{ master.values()[0] }}"
    - restart_splunk: True
    - require:
      - sls: splunk.common

{% set slaves = salt['publish.publish']('role:splunk-cluster-slave', 'splunk.get_mgmt_uri', None, 'grain') %}
{% if slaves %}
  {% for host,uri in slaves.iteritems() %}

set_fwd_server_{{ host }}:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/data/outputs/tcp/server
    - body:
        name: {{ uri }}
    - require:
      - splunk: install-splunk

  {% endfor %}
{% endif %}
