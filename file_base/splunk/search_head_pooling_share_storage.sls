#{% from "nfs/map.jinja" import nfs with context %}

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

#nfs-service:
#  service.running:
#    - name: {{ nfs.service_name }}
#    - enable: True
{% endif %}
