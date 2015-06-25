{% for dir, opts in salt['pillar.get']('nfs:server:exports').items() -%}
{{ dir }}:
  file.directory:
  	- mode: 777
  	- makedirs: True
{% endfor -%}
