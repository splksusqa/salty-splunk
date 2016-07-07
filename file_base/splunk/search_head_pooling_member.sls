{% if grains['os'] != 'Windows' %}
include:
  - nfs.client
  - splunk.indexer

{% for server, ips in salt['mine.get']('role:search_head_pooling_share_storage', 'network.ip_addrs', 'grain').items() %}
/opt/shp_share:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 777
    - recurse:
      - user
      - group
      - mode
  mount.mounted:
    - device: {{ ips[0] }}:/opt/shp_share
    - fstype: nfs
    - persist: True
  require:
    - file: /opt/shp_share
{% endfor %}

stop_splunk:
  module.run:
    - name: splunk.cli
    - command: stop -f

setup_shp:
  module.run:
     - name: splunk.cli
     - command: 'pooling enable /opt/shp_share'
     - require:
       - module: stop_splunk

{% set splunk_home = grains['splunk_home'] %}
copy_user_app:
  cmd.run:
    # splunk_home
    - name: |
        cp -r -n {{ splunk_home }}/etc/users /opt/shp_share
        cp -r -n {{ splunk_home }}/etc/apps /opt/shp_share
    - require:
      - module: setup_shp

start_splunk:
  module.run:
    - name: splunk.cli
    - kwargs:
         command: start
    - require:
      - cmd: copy_user_app

{% endif %}