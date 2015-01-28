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
