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

{% set hostip = salt['mine.get']('role:search_head_pooling_share_storage', 'fqdn_ip4', 'grain')[0] %}
/opt/shp_share
  mount.mounted:
    - device: {{ hostip }}:/opt/shp_share
    - fstype: nfs
    - persist: True
  require:
    - file: /opt/shp_share

{% endif %}