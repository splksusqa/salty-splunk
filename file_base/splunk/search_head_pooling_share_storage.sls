{% if grains['os'] != 'Windows' %}
include:
  - nfs.server

/opt/shp_share:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 777
    - recurse:
      - user
      - group
      - mode

{% endif %}
