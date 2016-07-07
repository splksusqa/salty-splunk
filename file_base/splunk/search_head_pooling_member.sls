{% if grains['os'] != 'Windows' %}
include:
  - nfs.client

/opt/shp_share:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 777
    - recurse:
      - user
      - group
      - mode

{% for server, ips in salt['mine.get']('role:search_head_pooling_share_storage', 'network.ip_addrs', 'grain').items() %}
/opt/shp_share
  mount.mounted:
    - device: {{ ips[0] }}:/opt/shp_share
    - fstype: nfs
    - persist: True
  require:
    - file: /opt/shp_share

{% endif %}