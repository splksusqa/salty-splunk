# common settings
# issue about merging pillars: https://github.com/saltstack/salt/issues/3991
system:
  {% if grains['kernel'] == 'Linux'%}
  user: root
  files_dir: /tmp/salt_files/
  {% elif grains['kernel'] == 'Windows'%}
  # Windows does not support runas functionality in cmd.run,
  # so we cant run splunk commands as another user.
  user: Aministrator
  files_dir: 'C:\temp\salt_files\'
  {% endif %}


splunk:
  splunkd_port: 8089
  splunkweb_port: 8000
  auth: 'admin:changeme'
  start_after_install: True # It's calling splunk.start, not using LAUNCHSPLUNK
  version: 6.1.6
  build: ''
  fetcher_url: http://r.susqa.com/cgi-bin/splunk_build_fetcher.py
  pkg_released: False
  instances: 1

  {% if grains['kernel'] == 'Linux'%}
  home: /opt/splunk
  pkg: Linux-x86_64.tgz
  {% elif grains['kernel'] == 'Windows' %}
  home: C:\Program Files\Splunk
  pkg: x64-release.msi
  {% endif %}

  {% if grains['role'] == 'splunk-universal-fwd' %}
  type: splunkforwarder
  {% else %}
  type: splunk
  {% endif %}

  install_flags:
  # http://docs.splunk.com/Documentation/Splunk/latest/Installation/InstallonWindowsviathecommandline#Supported_flags
  # Windows: quiet and AGREETOLICENSE are hard coded in install function
  # and INSTALLDIR is defined as pillar['splunk']['home']
    {% if grains['kernel'] == 'Windows' %}
    LAUNCHSPLUNK: 0
    {% endif %}

  listen:
    splunktcp: 9996
    tcp: 9997
    udp: 9998


