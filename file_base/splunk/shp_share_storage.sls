{% if grains['os_family'] == 'Windows'%}
{% set win_domain = pillar['win_domain']['domain_name'] %}
{% set win_user = pillar['win_domain']['username'] %}
{% set win_pwd = pillar['win_domain']['password'] %}

C:\shp_share:
  file.directory:
    - makedirs: True

setup-shareing:
  cmd.run:
    - name: >
        net share shp_share="c:\shp_share" "/GRANT:tsplkad.com\administrator,Full" &
        icacls "c:\shp_share" /grant {{ win_domain }}\{{ win_user }}:(OI)(CI)F /T
    - require:
      - file: C:\shp_share

{% else %}

include:
  - nfs.server

/opt/shp_share:
  file.directory:
    - user: nobody
    - group: nogroup
    - dir_mode: 777
    - makdirs: True

{% endif %}

update-mine-for-ip:
  module.run:
    - name: mine.update