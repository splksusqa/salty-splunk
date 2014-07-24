install-splunk:
  splunk:
    - installed
    - source: {{ pillar['splunk']['pkg'] }}
    - installer_flags: {{ pillar['installer_flags'] }}
    - splunk_home: {{ pillar['splunk']['home'] }}


set-cluster:
  splunk:
    - set_role
    - mode: cluster-master
