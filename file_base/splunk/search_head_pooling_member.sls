{% if grains['os'] != 'Windows' %}
include:
  - nfs.client
{% endif %}