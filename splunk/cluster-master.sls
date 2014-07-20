cluster-master:
  pkg:
    - installed
    - name: splunk
    {% if grains['os'] == 'Windows' %}
    - sources:
      - {{ pillar['splunk-version'] }}: http://releases.qa/{{ pillar['splunk-version'] }}/windows/splunk-{{ pillar['splunk-version'] }}-{{ pillar['splunk-build'] }}-x64-release.msi
    {% elif grains['os'] == 'Ubuntu' %}
    - sources: http://releases.qa/{{ pillar['splunk-version'] }}/linux/splunk-{{ pillar['splunk-version'] }}-{{ pillar['splunk-build'] }}-linux-2.6-amd64.deb
    {% endif %}

  splunk:
    - set_role
    - mode: cluster-master
