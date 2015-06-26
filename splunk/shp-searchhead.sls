include:
  - splunk.common
  - nfs.client

{% set share_folder = "/srv/splunk_share" %}
{% set splunk_home = salt['pillar.get']('splunk.home') %}
{% set share_apps_folder = pillar['splunk']['home'] ~ "/etc/apps" %}
{% set share_users_folder = pillar['splunk']['home'] ~ "/etc/users" %}
{% for r in grains['role'] if r == 'splunk-shp-init-folder' %}
{% set is_init_folder_role = True %}
{% endif %}

stop-splunk:
  module.run:
    - name: splunk.stop
    - require:
      - sls: splunk.common


setup-shp:
  splunk.configured:
    - interface: cli
    - command: pooling enable {{ share_folder }}
    - require:
      - module: stop-splunk

{% if is_init_folder_role %}
copy-apps-folder:
  module.run:
    - name: cmd.run
    - cmd: "/bin/cp -r {{ share_apps_folder }}/* {{ share_folder }}/etc/apps -f"
    - require:
      - splunk: setup-shp

copy-user-folder:
  module.run:
    - name: cmd.run
    - cmd: "/bin/cp -r {{ share_users_folder }}/* {{ share_folder }}/etc/users -f"
    - require:
      - splunk: setup-shp
{% endif %}

start-splunk:
  module.run:
    - name: splunk.start
    - require:
      - splunk: setup-shp
      {% if is_init_folder_role %}
      - module: copy-apps-folder
      - module: copy-user-folder
      {% endif %}

{% set nfs_ip = salt['publish.publish']('role:nfsserver', 'network.ip_addrs', None, 'grain').values()[0][0] %}
{% for dir, opts in salt['pillar.get']('nfs:server:exports').items() -%}
{{ share_folder }}:
  mount.mounted:
    - device: "{{ nfs_ip }}:{{ dir }}"
    - fstype: nfs
    - mkmnt: True
    - opts:
      - defaults
{% endfor -%}