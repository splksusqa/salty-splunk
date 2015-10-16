
# disable IE sec
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Active Setup\Installed Components\IsInstalled:
  reg.present:
    - vdata: 0
    - vtype: REG_DWORD