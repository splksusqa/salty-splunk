include:
  - splunk.common
  - nfs.client

{% set share_folder = "/srv/splunk_share" %}
{% set splunk_home = salt['pillar.get']('splunk.home') %}

stop-splunk:
  module.run:
    - name: splunk.stop
    - require:
      - sls: splunk.common


setup-shp:
  splunk.configured:
    - interface: cli
    - command: pooling enable {{ share_folder }}
    - require:
      - module: stop-splunk

copy-apps-folder:
  file.recurse:
    - name: {{ share_folder }}/etc/apps
    - source: {{ pillar['splunk']['home'] }}/etc/apps
    - dir_mode: 777
    - include_empty: True

copy-user-folder:
  file.recurse:
    - name: {{ share_folder }}/etc/users
    - source: {{ pillar['splunk']['home'] }}/etc/users
    - dir_mode: 777
    - include_empty: True

start-splunk:
  module.run:
    - name: splunk.start
    - require:
      - splunk: setup-shp
      - file: copy-apps-folder
      - file: copy-user-folder

{% set nfs_ip = salt['publish.publish']('role:nfsserver', 'network.ip_addrs', None, 'grain').values()[0][0] %}
{% for dir, opts in salt['pillar.get']('nfs:server:exports').items() -%}
{{ share_folder }}:
  mount.mounted:
    - device: "{{ nfs_ip }}:{{ dir }}"
    - fstype: nfs
    - mkmnt: True
    - opts:
      - defaults
{% endfor -%}