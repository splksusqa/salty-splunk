{% if grains['os_family'] == 'Windows'%}
{% set win_domain = pillar['win_domain']['domain_name'] %}
{% set win_user = pillar['win_domain']['username'] %}
{% set win_pwd = pillar['win_domain']['password'] %}

C:\shp_share:
  file.directory:
    - makedirs: True

setup-shareing:
  splunk.create_shared_folder:
    - shared_name: shp_share
    # net share command accept not backslash
    - folder_path: c:\shp_share
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