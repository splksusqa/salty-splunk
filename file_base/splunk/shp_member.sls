# docs of shp
# http://docs.splunk.com/Documentation/Splunk/6.4.1/DistSearch/Createasearchheadpool

{% set ip_dict = salt['mine.get']('role:search-head-pooling-share-storage',
                                  'network.ip_addrs', 'grain')
%}
{% set sever, ips = ip_dict.popitem() %}
{% set share_storage_ip = ips[0] %}

{% if ( grains['os'] == 'Windows' %}
{% set share_folder_path = '\\\\' + share_storage_ip + '\\shp_share' %}
{% set map_drive = 'x' %}

include:
  - splunk.indexer

win-domain-info-must-have:
  test.check_pillar:
    - present:
      - win_domain

map-drive:
  cmd.run:
    - name: >
        net use {{ map_drive }}: "{{ share_folder_path }}"
        /user:{{ pillar['win_domain']['domain_name'] }}\
        {{ pillar['win_domain']['username'] }} {{ pillar['win_domain']['password'] }}
    - require:
      - test: win-domain-info-must-have

# non windows system
{% else %}
{% set share_folder_path = '/opt/shp_share' %}

include:
  - nfs.client
  - splunk.indexer

{{ share_folder_path }}:
  file.directory:
    - user: nobody
    - group: nogroup
    - dir_mode: 777
  mount.mounted:
    - device: {{ share_storage_ip }}:/opt/shp_share
    - fstype: nfs
    - persist: True
  require:
    - file: {{ share_folder_path }}
{% endif %}

stop_splunk:
  module.run:
    - name: splunk.cli
    - command: stop
    {% if grains['os'] == 'Windows' %}
    - require:
      - cmd: map-drive
    {% endif %}

setup_shp:
  module.run:
     - name: splunk.cli
     - command: 'pooling enable {{ share_folder_path }}'
     - require:
       - module: stop_splunk

{% set splunk_home = grains['splunk_home'] %}
copy_user_app:
  cmd.run:
    {% if grains['os'] == 'Windows' %}
    - name: |
        robocopy "{{ splunk_home }}\etc\users" {{ map_drive }}:\etc\users /e /xo
        robocopy "{{ splunk_home }}\etc\apps" {{ map_drive }}:\etc\apps /e /xo
    - require:
      - module: setup_shp
      - cmd: map-drive
    {% else %}
    - name: |
        cp -r -n {{ splunk_home }}/etc/users /opt/shp_share/etc
        cp -r -n {{ splunk_home }}/etc/apps /opt/shp_share/etc
    - require:
      - module: setup_shp
    {% endif %}

start_splunk:
  module.run:
    - name: splunk.cli
    - command: start
    - require:
      - cmd: copy_user_app

