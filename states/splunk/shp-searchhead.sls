include:
  - splunk.common
  - nfs.client

{% set share_folder = "/srv/splunk_share" %}
{% set splunk_home = salt['pillar.get']('splunk.home') %}
{% set share_apps_folder = pillar['splunk']['home'] ~ "/etc/apps" %}
{% set share_users_folder = pillar['splunk']['home'] ~ "/etc/users" %}
{% set is_init_folder_role = [] %}
{% for r in grains['role'] %}
  {% if r == 'splunk-shp-init-folder' %}
    {% do is_init_folder_role.append(1) %}
  {% endif %}
{% endfor %}

# 1st step, mount share fodler from nfs server
{% set nfs_ip = salt['publish.publish']('role:nfsserver', 'network.ip_addrs', None, 'grain').values()[0][0] %}
{% for dir, opts in salt['pillar.get']('nfs:server:exports').items() -%}
{{ share_folder }}:
  mount.mounted:
    - device: "{{ nfs_ip }}:{{ dir }}"
    - fstype: nfs
    - mkmnt: True
    - order: 1
    - opts:
      - defaults
{% endfor -%}

# 2nd stop the splunk
stop-splunk:
  module.run:
    - name: splunk.stop
    - order: 1
    - require:
      - sls: splunk.common

{% if is_init_folder_role %}
{{ share_folder }}/etc/apps:
  file.directory:
    - mode: 777
    - makedirs: True
    - order: 2
    # - require:
    #   - module: stop-splunk
    #   - mount: {{ share_folder }}

copy-apps-folder:
  module.run:
    - name: cmd.run
    - cmd: "cp -r -u {{ share_apps_folder }}/* {{ share_folder }}/etc/apps"
    - order: 3
  # file.copy:
  #   - name: {{ share_folder }}/etc/apps
  #   - source: {{ share_apps_folder }}
  #   - makedirs: True
  #   - preserve: True
  #   - require:
  #     - module: stop-splunk
  #     - mount: {{ share_folder }}

{{ share_folder }}/etc/users:
  file.directory:
    - mode: 777
    - makedirs: True
    - order: 2

copy-user-folder:
  module.run:
    - name: cmd.run
    - cmd: "cp -r -u {{ share_users_folder }}/* {{ share_folder }}/etc/users"
    - order: 3
  # file.copy:
  #   - name: {{ share_folder }}/etc/users
  #   - source: {{ share_users_folder }}
  #   - makedirs: True
  #   - preserve: True
  #   - require:
  #     - module: stop-splunk
  #     - mount: {{ share_folder }}
{% endif %}

setup-shp:
  splunk.configured:
    - interface: cli
    - command: pooling enable {{ share_folder }}
    - require:
      - module: stop-splunk
      {% if is_init_folder_role %}
      - module: copy-apps-folder
      - module: copy-user-folder
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
