splunk:
  version: 6.1.3
  build: 217765

  {% if grains['os'] == 'RedHat'%}
  home: /opt/splunk
  pkg: http://172.31.25.233/6.1.3/linux/splunk-6.1.3-217765-linux-2.6-x86_64.rpm

  {% elif grains['os'] == 'Ubuntu' %}
  home: /opt/splunk
  pkg: http://172.31.25.233/6.1.3/linux/splunk-6.1.3-217765-linux-2.6-amd64.deb

  {% elif grains['os'] == 'Windows' %}
  home: C:\Program Files\Splunk
  pkg: http://172.31.25.233/6.1.3/windows/splunk-6.1.3-217765-x64-release.msi
  {% endif %}

installer_flags:
# http://docs.splunk.com/Documentation/Splunk/latest/Installation/InstallonWindowsviathecommandline#Supported_flags
# Windows: quiet and AGREETOLICENSE are hard coded in install function
# and INSTALLDIR is defined as pillar['splunk']['home']
  {% if grains['os'] == 'Windows' %}
  LAUNCHSPLUNK: 0
  {% endif %}

