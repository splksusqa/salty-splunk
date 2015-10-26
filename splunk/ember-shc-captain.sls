boostrap-shc:
  splunk:
    - configured
    - interface: cli
    - command: "bootstrap shcluster-captain"
    - params:
        servers_list: {{ salt['publish.publish']('role:splunk-ember-shc-member', 'splunk.get_mgmt_uri', None, 'grain').values()|join(",") }}

