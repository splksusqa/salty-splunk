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

/opt/shp_share:
  mount.mounted:
    - device: /dev/xvda
    - fstype: nfs
    - persist: True
  require:
    - file: /opt/shp_share

{% endif %}