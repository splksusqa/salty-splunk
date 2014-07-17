cluster-slave:

  splunk:
    - installed
    - role: cluster-searchhead
    - master: https://master:28089