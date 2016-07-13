change-dns:
  module.run:
    - name: ip.set_static_dns
    - iface: Local Area Connection
    - addrs:
      - {{ pillar['win_domain']['dns1'] }}
      - {{ pillar['win_domain']['dns2'] }}

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