
{% if not grains['kernel'] == 'Windows'%}
install-psutil:
  pkg:
    - installed
    - name: python-psutil
{% endif %}


install-splunk:
  splunk:
    - installed
    - source:              {{ pillar['splunk']['pkg'] }}
    - install_flags:       {{ pillar['splunk']['install_flags'] }}
    - splunk_home:         {{ pillar['splunk']['home'] }}
    - start_after_install: {{ pillar['splunk']['start_after_install'] }}


set-splunkd-port:
  splunk:
    - splunkd_port
    - port:   {{ pillar['splunk']['splunkd_port'] }}
    - require:
      - splunk: install-splunk


set-splunkweb-port:
  splunk:
    - splunkweb_port
    - port: {{ pillar['splunk']['splunkweb_port'] }}
    - require:
      - splunk: install-splunk

enable_remote_access:
  splunk:
    - rest_configured
    - method: post
    - uri: services/properties/server/general
    - body:
        allowRemoteLogin: always
    - require:
      - splunk: install-splunk
