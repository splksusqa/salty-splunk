boostrap-shc:
  splunk:
    - configured
    - interface: cli
    - command: "bootstrap shcluster-captain"
    - params:
        servers_list: {{ salt['publish.publish']('*-shc-*', 'splunk.get_mgmt_uri').values()|join(",") }}
