install-splunk:
  splunk:
    - installed
    - source:         {{ pillar['splunk']['pkg'] }}
    - install_flags:  {{ pillar['splunk']['install_flags'] }}
    - splunk_home:    {{ pillar['splunk']['home'] }}


set-splunkd-port:
  splunk:
    - splunkd_port
    - port:   {{ pillar['splunk']['splunkd_port'] }}


set-splunkweb-port:
  splunk:
    - splunkweb_port
    - port: {{ pillar['splunk']['splunkweb_port'] }}


enable_remote_access:
  splunk:
    - remote_access_enabled
    - method: rest
    - endpoint: services/properties/server/general
    - setting:
