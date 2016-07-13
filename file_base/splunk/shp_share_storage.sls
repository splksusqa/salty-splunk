{% if grains['os'] != 'Windows' %}
include:
  - nfs.server

/opt/shp_share:
  file.directory:
    - user: nobody
    - group: nogroup
    - dir_mode: 777
    - makdirs: True

{% else %}

C:\shp_share:
  file.directory:
    - user: nobody
    - group: nogroup
    - makedirs: True

setup-shareing:
  cmd.run:
    - name: net share shp_share=c:\shp_share /GRANT:Everyone,FULL

{% endif %}
