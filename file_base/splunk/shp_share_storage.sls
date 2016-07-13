{% if grains['os'] != 'Windows' %}
include:
  - nfs.server

update-mine-for-ip:
  module.run:
    - name: mine.update

/opt/shp_share:
  file.directory:
    - user: nobody
    - group: nogroup
    - dir_mode: 777
    - makdirs: True

{% else %}

C:\shp_share:
  file.directory:
    - makedirs: True

setup-shareing:
  cmd.run:
    - name: net share shp_share=c:\shp_share /GRANT:Everyone,FULL
    - require:
      - file: C:\shp_share

{% endif %}
