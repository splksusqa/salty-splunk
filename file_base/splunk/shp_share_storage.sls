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

{% else %}

Local Area Connection #2:
  network.managed:
    - dns_proto: static
    - dns_servers:
      - 172.31.36.77
      - 172.31.14.80

{% endif %}
