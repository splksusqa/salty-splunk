set-role:
  splunk:
    - role_configured
    - method: rest
    - endpoint: services/search/distributed/peers
    - setting:
        distributedSearch:
          servers: idx1, idx2, idx3
