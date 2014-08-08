install-splunk:
  splunk:
    - installed
    - source:         {{ pillar['splunk']['pkg'] }}
    - install_flags:  {{ pillar['splunk']['install_flags'] }}
    - splunk_home:    {{ pillar['splunk']['home'] }}


set-splunkd-port:
  splunk:
    - set_splunkd_port
    - splunkd_port:   {{ pillar['splunk']['splunkd_port'] }}


set-splunkweb-port:
  splunk:
    - set_splunkweb_port
    - splunkweb_port: {{ pillar['splunk']['splunkweb_port'] }}