include:
  - splunk.common

{% for mgmt in salt['publish.publish']('role:*slave', 'splunk.get_listening_uri', 'type=splunktcp', 'grain').values() %}

set_fwd_server_{{mgmt}}:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/data/outputs/tcp/server
    - body:
        name: {{mgmt}}
    - require:
      - splunk: install-splunk

{% endfor %}