
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