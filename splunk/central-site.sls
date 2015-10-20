
# disable IE sec
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Active Setup\Installed Components\{A509B1A7-37EF-4b3f-8CFC-4F3A74704073}:
  reg.present:
    - vname: IsInstalled
    - vdata: 0
    - vtype: REG_DWORD

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Active Setup\Installed Components\{A509B1A8-37EF-4b3f-8CFC-4F3A74704073}:
  reg.present:
    - vname: IsInstalled
    - vdata: 0
    - vtype: REG_DWORD

# disable firewall
disable_firewall:
  win_firewall.disabled:
    - name: disable_win_firewall

# ready for adding to qatw-ipv6.com
Ethernet:
  network.managed:
    - dns_proto: static
    - dns_servers:
      - 10.140.28.88
      - 10.140.6.24
    - ip_proto: dhcp

# ntp server for sync time with AD domain
win_ntp:
  ntp.managed:
    - servers:
      - ntp1.sv.splunk.com

# add to domain
# install wget
# install python
# tempdir

# enable msi log
# TODO for every splunk installation only
# https://support.microsoft.com/en-us/kb/2545723
# salt -G 'role:central-site' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\Policies\Microsoft\Windows\Installer' 'Logging' 'voicewarmupx'
# salt -G 'role:central-site' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\Policies\Microsoft\Windows\Installer' 'Debug' 7 'REG_DWORD'
# salt -G 'role:central-site' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Trace' 'Flags' 16 'REG_DWORD'
# salt -G 'role:central-site' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Trace' 'Level' 4 'REG_DWORD'
