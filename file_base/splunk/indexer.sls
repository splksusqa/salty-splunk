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
    - kwargs:
        length: 30

allow_remote_login:
  module.run:
    - name: splunk.allow_remote_login
    - require:
      - splunk: install-splunk
