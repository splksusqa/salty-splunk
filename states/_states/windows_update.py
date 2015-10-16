import salt.exceptions

def _read_winlogon_key(key_name):
    return __salt__['reg.read_key']('HKEY_LOCAL_MACHINE',
                                    'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon',
                                    key_name)


def _set_win_update_key(key, value):
    return __salt__['reg.set_key']('HKEY_LOCAL_MACHINE',
                                   'SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update',
                                   key,
                                   value,
                                   'REG_DWORD')

def disable_auto_update(name, username, password):
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    _set_win_update_key('AUOptions', 1)