include:
  - splunk.common

enable-deploy-server:
  splunk:
  - cli_configured
  - command: "enable deploy-server"
  - require:
      - sls: splunk.common

create-serverclasses:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/deployment/server/serverclasses
    - body:
        name: {{ pillar['myServerClass']['name'] }}
        restartSplunkd:  {{ pillar['myServerClass']['restartSplunkd'] }}
        whitelist.0:  "{{ pillar['myServerClass']['whitelist.0'] }}"
    - require:
      - sls: splunk.common

# create an app folder 
"{{pillar['splunk']['home']}}/etc/deployment-apps/{{pillar['myServerClass']['deployAppName']}}":
  file.directory:
    - mode: 755
    - makedirs: True

add-deploy-app:
  splunk:
    - configured
    - interface: rest
    - method: post
    - uri: services/deployment/server/applications/{{ pillar['myServerClass']['deployAppName'] }}
    - body:
        serverclass: {{ pillar['myServerClass']['name'] }}
    - require:
      - sls: splunk.common

reload-deploy-server:
  splunk:
    - cli_configured
    - command: "reload deploy-server"
    - require:
      - sls: splunk.common