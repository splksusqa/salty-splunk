# common settings
# issue about merging pillars: https://github.com/saltstack/salt/issues/3991
splunk:
  version: 6.1.3
  build: 217765
  splunkd_port: 9000
  splunkweb_port: 9089
  auth: admin:changeme

  {% if grains['os'] == 'RedHat'%}
  home: /opt/splunk
  pkg: http://172.31.25.233/6.1.3/linux/splunk-6.1.3-220630-Linux-x86_64.tgz

  {% elif grains['os'] == 'Ubuntu' %}
  home: /opt/splunk
  pkg: http://172.31.25.233/6.1.3/linux/splunk-6.1.3-220630-Linux-x86_64.tgz

  {% elif grains['os'] == 'Windows' %}
  home: C:\Program Files\Splunk
  pkg: http://172.31.25.233/6.1.3/windows/splunk-6.1.3-217765-x64-release.msi
  {% endif %}

  install_flags:
  # http://docs.splunk.com/Documentation/Splunk/latest/Installation/InstallonWindowsviathecommandline#Supported_flags
  # Windows: quiet and AGREETOLICENSE are hard coded in install function
  # and INSTALLDIR is defined as pillar['splunk']['home']
    {% if grains['os'] == 'Windows' %}
    LAUNCHSPLUNK: 0
    {% endif %}


s3:
  keyid:
  key:
  service_url: s3.amazonaws.com