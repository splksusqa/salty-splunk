include:
  - splunk.common

install-splunk:
  splunk:
    - installed
    - fetcher_arg: {{ pillar['version'] }}
    - require:
      - sls: splunk.common

#TODO find out why Splunk might fail by timeout config allow remote login
sleep_after_install_splunk:
  module.run:
    - name: test.sleep
    - length: 30
    - onchanges:
      - splunk: install-splunk

allow_remote_login:
  module.run:
    - name: splunk.allow_remote_login
    - onchanges:
      - module: sleep_after_install_splunk
