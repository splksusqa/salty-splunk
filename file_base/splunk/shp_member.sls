# docs of shp
# http://docs.splunk.com/Documentation/Splunk/6.4.1/DistSearch/Createasearchheadpool

{% set ip_dict = salt['mine.get']('role:search-head-pooling-shared-storage',
                                  'network.ip_addrs', 'grain')
%}
{% set sever, ips = ip_dict.popitem() %}
{% set share_storage_ip = ips[0] %}

{% if grains['os'] == 'Windows' %}
{% set share_folder_path = '\\\\' + share_storage_ip + '\\shp_share' %}

include:
  - splunk.indexer

{% set win_domain = pillar['win_domain']['domain_name'] %}
{% set win_user = pillar['win_domain']['username'] %}
{% set win_pwd = pillar['win_domain']['password'] %}

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

setup_shp:
  splunk.enable_search_head_pooling:
     - shared_folder: {{ share_folder_path }}
     - require:
       - module: stop_splunk

{% set splunk_home = grains['splunk_home'] %}
copy_user_app:
# use module run because robocopy would return exit code 1
# for new added folder
  {% if grains['os'] == 'Windows' %}
  splunk.copy_shp_shared_files:
    - name: cmd.run
    - splunk_home: {{ splunk_home }}
    - shared_folder_path: {{ share_folder_path }}
    - runas: {{ win_domain }}\{{ win_user }}
    - password: {{ win_pwd }}
    - onchanges:
      - splunk: setup_shp
  {% else %}
  cmd.run:
    - name: >
        cp -r -n {{ splunk_home }}/etc/users /opt/shp_share/etc &&
        cp -r -n {{ splunk_home }}/etc/apps /opt/shp_share/etc
    - onchanges:
      - splunk: setup_shp
  {% endif %}

start_splunk:
  module.run:
    - name: splunk.cli
    - command: start
    - require:
      - module: stop_splunk
    - order: last

