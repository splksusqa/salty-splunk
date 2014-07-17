splunk-cluster-searchhead:
  pkg:
    - installed
    - name: splunk
    {% if grains['os'] == 'Windows' %}
    - version:
      - {{ pillar['splunk-version'] }}: http://releases.qa/{{ pillar['splunk-version'] }}/windows/splunk-6.1.3-217765-x64-release.msi
    {% elif grains['os'] == 'Ubuntu' %}
    - sources: http://releases.qa/{{ pillar['splunk-version'] }}/linux/splunk-6.1.3-217765-linux-2.6-amd64.deb
    {% endif %}

  splunk:
    - set_role
    - mode: cluster-searchhead
    - master: https://master:28089