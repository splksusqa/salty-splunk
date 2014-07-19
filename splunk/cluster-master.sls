cluster-master:
#  pkg
#    installed:
#    - name: splunk
#    {% if grains['os'] == 'Windows' %}
#    - sources:
#      - {{ pillar['splunk-version'] }}: http://releases.qa/{{ pillar['splunk-version'] }}/windows/splunk-6.1.3-217765-x64-release.msi
#    {% elif grains['os'] == 'Ubuntu' %}
#    - sources: http://releases.qa/{{ pillar['splunk-version'] }}/linux/splunk-6.1.3-217765-linux-2.6-amd64.deb
#    {% endif %}
  splunk:
    installed:
    - mode: master