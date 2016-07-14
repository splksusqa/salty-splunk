{% set interfaces = salt.network.interfaces_names() %}

win-domain-info-must-have:
  test.check_pillar:
    - present:
      - win_domain

change-dns:
  module.run:
    - name: ip.set_static_dns
    - iface: {{ interfaces[0] }}
    - addrs:
      - {{ pillar['win_domain']['dns1'] }}
      - {{ pillar['win_domain']['dns2'] }}
    - require:
      - test: win-domain-info-must-have

join-domain:
  module.run:
    - name: system.join_domain
    - domain: {{ pillar['win_domain']['domain_name'] }}
    - username: {{ pillar['win_domain']['username'] }}
    - password: {{ pillar['win_domain']['password'] }}
    - restart: True
    - order: last
    - require:
      - module: change-dns