
{% if grains['os'] != 'Windows' %}
python-pip:
  pkg:
    - installed
{% endif %}
