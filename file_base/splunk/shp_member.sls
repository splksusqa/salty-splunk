# docs of shp
# http://docs.splunk.com/Documentation/Splunk/6.4.1/DistSearch/Createasearchheadpool

{% set ip_dict = salt['mine.get']('role:search-head-pooling-share-storage',
                                  'network.ip_addrs', 'grain')
%}
{% set sever, ips = ip_dict.popitem() %}
{% set share_storage_ip = ips[0] %}

{% if grains['os'] == 'Windows' %}
{% set share_folder_path = '\\\\' + share_storage_ip + '\\shp_share' %}
#{% set map_drive = 'x' %}

include:
  - splunk.indexer

{% set win_domain = pillar['win_domain']['domain_name'] %}
{% set win_user = pillar['win_domain']['username'] %}
{% set win_pwd = pillar['win_domain']['password'] %}
#map-drive:
#  cmd.run:
#    - name: >
#        net use {{ map_drive }}: "{{ share_folder_path }}"
#        /user:{{ win_domain }}\{{ win_user }} {{ win_pwd }}

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
        robocopy "{{ splunk_home }}\etc\users" "{{ share_folder_path }}:\etc\users" /e /xo /NFL
        robocopy "{{ splunk_home }}\etc\apps" "{{ share_folder_path }}:\etc\apps" /e /xo /NFL
    - runas: {{ win_domain }}\{{ win_user }}
    - password: {{ win_pwd }}
    - require:
      - module: setup_shp
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

