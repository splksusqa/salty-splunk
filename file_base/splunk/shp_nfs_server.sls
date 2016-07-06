{% if grains['os'] != 'Windows' %}
include:
  - nfs.server
{% endif %}
