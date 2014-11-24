
{% if not grains['kernel'] == 'Windows'%}
install-psutil:
  pkg:
    - installed
    - name: python-psutil
{% endif %}


install-splunk:
  splunk:
    - installed
    - splunk_home:         {{ pillar['splunk']['home'] }}
    - pkg:                 {{ pillar['splunk']['pkg'] }}
    - version:             {{ pillar['splunk']['version'] }}
    - build:               {{ pillar['splunk']['build'] }}
    - fetcher_url:         {{ pillar['splunk']['fetcher_url'] }}
    - pkg_released:        {{ pillar['splunk']['pkg_released'] }}
    - instances:           {{ pillar['splunk']['instances'] }}
    - install_flags:       {{ pillar['splunk']['install_flags'] }}
    - start_after_install: {{ pillar['splunk']['start_after_install'] }}


set-splunkd-port:
  splunk:
    - splunkd_port
    - port:   {{ pillar['splunk']['splunkd_port'] }}
    - require:
      - splunk: install-splunk


{% if not (grains['role'] == 'universal-forwarder' or grains['role'] == 'light-forwarder') %}
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


listen_splunktcp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/tcp/cooked
    - body:
        name: 9996
    - require:
      - splunk: install-splunk


listen_tcp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/tcp/raw
    - body:
        name: 9997
    - require:
      - splunk: install-splunk


listen_udp:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: servicesNS/nobody/search/data/inputs/udp
    - body:
        name: 9998
    - require:
      - splunk: install-splunk




