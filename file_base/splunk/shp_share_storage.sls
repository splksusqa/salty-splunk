{% if ( grains['os_family'] == 'Windows' and
        pillar['win_domain']['username'] is not none ): %}

C:\shp_share:
  file.directory:
    - makedirs: True

setup-shareing:
  cmd.run:
    - name: net share shp_share=c:\shp_share
    - require:
      - file: C:\shp_share

{% elif grains['os_family'] == 'Linux' %}

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

# dummy
always-passes:
  test.succeed_without_changes:
    - name: foo

{% endif %}
