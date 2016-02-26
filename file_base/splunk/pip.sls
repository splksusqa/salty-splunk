
{% if grains['os'] != 'Windows' %}
python-pip:
  pkg:
    - installed
{% endif %}

# have this state to provide empty state file under windows
dummy-states:
  test.succeed_without_changes:
    - name: foo