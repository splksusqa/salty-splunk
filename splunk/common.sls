install-splunk:
  splunk:
    - installed
    - source:         {{ pillar['splunk']['pkg'] }}
    - install_flags:  {{ pillar['splunk']['install_flags'] }}
    - splunk_home:    {{ pillar['splunk']['home'] }}
    - splunkd_port:   {{ pillar['splunk']['splunkd_port'] }}
    - splunkweb_port: {{ pillar['splunk']['splunkweb_port'] }}