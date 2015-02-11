boostrap-shc:
  splunk:
    - configured
    - interface: cli
    - command: "bootstrap shcluster-captain"
    - params:
        servers_list: {{ salt['publish.publish']('role:splunk-shc-member', 'splunk.get_mgmt_uri', None, 'grain').values()|join(",") }}

