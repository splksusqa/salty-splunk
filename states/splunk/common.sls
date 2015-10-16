
{% if not grains['kernel'] == 'Windows'%}
install-psutil:
  pkg:
    - installed
    - name: python-psutil
{% endif %}

# create splunk home folder
{% if grains['kernel'] == 'Linux'%}
{{ pillar['splunk']['home'] }}:
  file.directory:
    - mode: 777
    - makedirs: True
{% endif %}

install-splunk:
  splunk:
    - installed
    - splunk_home:         {{ pillar['splunk']['home'] }}
    - pkg:                 {{ pillar['splunk']['pkg'] }}
    - version:             {{ pillar['splunk']['version'] }}
    - build:               {{ pillar['splunk']['build'] }}
    - type:                {{ pillar['splunk']['type'] }}
    - fetcher_url:         {{ pillar['splunk']['fetcher_url'] }}
    - pkg_released:        {{ pillar['splunk']['pkg_released'] }}
    - instances:           {{ pillar['splunk']['instances'] }}
    - install_flags:       {{ pillar['splunk']['install_flags'] }}
    - start_after_install: {{ pillar['splunk']['start_after_install'] }}
    {% if grains['kernel'] == 'Linux'%}
    - require:
      - file: {{ pillar['splunk']['home'] }}
    {% endif %}


set-splunk-server-name:
  splunk:
    - configured
    - interface: conf
    - conf: server.conf
    - stanza:
        general:
          serverName: {{ grains['id'] }}
    - restart_splunk: True


set-splunkd-port:
  splunk:
    - splunkd_port
    - port:   {{ pillar['splunk']['splunkd_port'] }}
    - require:
      - splunk: install-splunk


{% if not (grains['role'] == 'splunk-universal-fwd' or grains['role'] == 'splunk-light-fwd') %}
set-splunkweb-port:
  splunk:
    - splunkweb_port
    - port: {{ pillar['splunk']['splunkweb_port'] }}
    - require:
      - splunk: install-splunk
{% endif %}


enable_remote_access:
  splunk:
    - rest_configured
    - method: post
    - uri: services/properties/server/general
    - body:
        allowRemoteLogin: always
    - require:
      - splunk: install-splunk


set-min-disk:
  splunk:
    - rest_configured
    - method: post
    - uri: services/server/settings/settings
    - body:
        minFreeSpace: 1000
    - require:
      - splunk: install-splunk

