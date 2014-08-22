# common settings
# issue about merging pillars: https://github.com/saltstack/salt/issues/3991
system:
  {% if grains['os'] == 'Ubuntu'%}
  user: root
  fs_root: /tmp/
  {% elif grains['os'] == 'RedHat'%}
  user: root
  fs_root: /tmp/
  {% elif grains['os'] == 'Windows'%}
  # Windows does not support runas functionality in cmd.run,
  # so we cant run splunk commands as another user.
  user: Aministrator
  fs_root: 'C:\'
  {% endif %}


splunk:
  splunkd_port: 8089
  splunkweb_port: 8000
  auth: 'admin:changeme'
  start_after_install: True # It's calling splunk.start, not using LAUNCHSPLUNK
  dataset: 's3://qasus_data/new_test_data/FoursquareData.txt'
  app: 's3://qasus_data/apps/sideview-utils-lgpl_135.tgz'
  #

  {% if grains['kernel'] == 'Linux'%}
  home: /opt/splunk
  pkg: http://r.susqa.com/6.1.3/linux/splunk-6.1.3-220630-Linux-x86_64.tgz

  {% elif grains['kernel'] == 'Windows' %}
  home: C:\Program Files\Splunk
  pkg: http://r.susqa.com/6.1.3/windows/splunk-6.1.3-220630-x64-release.msi
  {% endif %}


  install_flags:
  # http://docs.splunk.com/Documentation/Splunk/latest/Installation/InstallonWindowsviathecommandline#Supported_flags
  # Windows: quiet and AGREETOLICENSE are hard coded in install function
  # and INSTALLDIR is defined as pillar['splunk']['home']
    {% if grains['os'] == 'Windows' %}
    LAUNCHSPLUNK: 0
    AGREETOLICENSE: 'Yes'
    {% endif %}

monitoring:
  # default to blank, will get the ip of master, so splunk for monitoring should
  # be installed at master.
  splunk_ip:
  listen_port: 9997
  listen_schema: tcp

## used by s3fs (of salt) ##
s3.keyid:
s3.key:
s3.service_url: s3.amazonaws.com

# Apps:
# s3://splunk_apps/add-on-for-jira_201.tgz
# s3://splunk_apps/gen_data.tgz
# s3://splunk_apps/google-maps_113.tgz
# s3://splunk_apps/sideview-utils-lgpl_135.tgz
# s3://splunk_apps/sos-splunk-on-splunk_32.tgz
# s3://splunk_apps/splunk-add-on-for-unix-and-linux_503.tgz
# s3://splunk_apps/splunk-app-for-enterprise-security_311.tgz
# s3://splunk_apps/splunk-app-for-hadoopops_113.zip
# s3://splunk_apps/splunk-db-connect_114.tgz
# s3://splunk_apps/splunk-for-google-app-engine_11.tgz
# s3://splunk_apps/splunk-for-palo-alto-networks_411.tgz
# s3://splunk_apps/splunk-hadoop-connect_121.tgz
# s3://splunk_apps/splunk-hadoop-connect_122.tgz
# s3://splunk_apps/splunk-on-splunk-sos-add-on-for-unix-and-linux_205.tgz
# s3://splunk_apps/splunk-on-splunk-sos-add-on-for-windows_233.tgz
# s3://splunk_apps/splunk-technology-add-on-for-hadoopops_111.tgz

#  app_source_sos_addon: s3://splunk_apps/splunk-add-on-for-unix-and-linux_503.tgz
#  app_dest_sos_addon: /tmp/splunk-add-on-for-unix-and-linux_503.tgz
#  app_source_sos: s3://splunk_apps/splunk-on-splunk-sos-add-on-for-unix-and-linux_205.tgz
#  app_dest_sos: /tmp/splunk-on-splunk-sos-add-on-for-unix-and-linux_205.tgz
