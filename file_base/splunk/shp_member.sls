# docs of shp
# http://docs.splunk.com/Documentation/Splunk/6.4.1/DistSearch/Createasearchheadpool

# 1 config search peer on each search head
include:
  - splunk.search_head

{% set server, ips = salt['mine.get']('role:search_head_pooling_share_storage', 'network.ip_addrs', 'grain').popitem() %}

{% if grains['os'] == 'Windows' %}
{% set share_folder_path = //ips[0]/shp_share %}

include:
  - splunk.indexer






# non windows system
{% else %}
{% set share_folder_path = /opt/shp_share %}

include:
  - nfs.client
  - splunk.indexer

{{ share_folder_path }}:
  file.directory:
    - user: nobody
    - group: nogroup
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
    - file: {{ share_folder_path }}


{% endif %}

stop_splunk:
  module.run:
    - name: splunk.cli
    - command: stop -f

setup_shp:
  module.run:
     - name: splunk.cli
     - command: 'pooling enable {{ share_folder_path }}'
     - require:
       - module: stop_splunk

{% set splunk_home = grains['splunk_home'] %}
copy_user_app:
  cmd.run:
    # splunk_home
    {% if grains['os'] == 'Windows' %}
    - name: |
        robocopy {{ splunk_home }}\etc\users {{ share_folder_path }}\etc /e /xo
        robocopy {{ splunk_home }}\etc\apps {{ share_folder_path }}\etc /e /xo
    {% else %}
    - name: |
        cp -r -n {{ splunk_home }}/etc/users /opt/shp_share/etc
        cp -r -n {{ splunk_home }}/etc/apps /opt/shp_share/etc
    {% endif %}
    - require:
      - module: setup_shp

start_splunk:
  module.run:
    - name: splunk.cli
    - command: start
    - require:
      - cmd: copy_user_app

