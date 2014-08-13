# common settings
# issue about merging pillars: https://github.com/saltstack/salt/issues/3991
splunk:
  version: 6.1.3
  build: 217765
  splunkd_port: 9000
  splunkweb_port: 9089
  username: admin
  password: changeme
  dataset_source: 's3://qasus_data/new_test_data/FoursquareData.txt'
  app_source: 's3://qasus_data/apps/sideview-utils-lgpl_135.tgz'


  {% if grains['kernel'] == 'Linux'%}

  home: /opt/splunk
  pkg: http://172.31.25.233/6.1.3/linux/splunk-6.1.3-220630-Linux-x86_64.tgz
  dataset_dest: /tmp/FoursquareData.txt
  app_dest: /tmp/sideview-utils-lgpl_135.tgz

  {% elif grains['kernel'] == 'Windows' %}
  home: C:\Program Files\Splunk
  pkg: http://172.31.25.233/6.1.3/windows/splunk-6.1.3-217765-x64-release.msi
  dataset_dest: 'C:\Temp\FoursquareData.txt'
  app_dest: 'C:\Temp\sideview-utils-lgpl_135.tgz'
  {% endif %}


  install_flags:
  # http://docs.splunk.com/Documentation/Splunk/latest/Installation/InstallonWindowsviathecommandline#Supported_flags
  # Windows: quiet and AGREETOLICENSE are hard coded in install function
  # and INSTALLDIR is defined as pillar['splunk']['home']
    {% if grains['os'] == 'Windows' %}
    LAUNCHSPLUNK: 0
    {% endif %}

## used by s3fs (of salt) ##
s3.keyid:
s3.key:
s3.service_url: s3.amazonaws.com
