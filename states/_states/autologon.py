import salt.exceptions
import logging

log = logging.getLogger(__name__)


def _read_winlogon_key(key_name):
    return __salt__['reg.read_key']('HKEY_LOCAL_MACHINE',
                                    'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon',
                                    key_name)


def _set_winlogon_key(key, value):
    return __salt__['reg.set_key']('HKEY_LOCAL_MACHINE',
                                   'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon',
                                   key,
                                   value,
                                   'REG_SZ')


def enable_user(name, username, password):
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    auto_admin_logon = _read_winlogon_key('AutoAdminLogon')
    log.info('original AutoAdminLogon: %s' % auto_admin_logon)
    default_user = _read_winlogon_key('DefaultUserName')
    log.info('original DefaultUserName: %s' % default_user)
    default_domain_name = _read_winlogon_key('DefaultDomainName')
    log.info('original DefaultDomainName: %s' % default_domain_name)
    default_password = _read_winlogon_key('DefaultPassword')
    log.info('original DefaultPassword: %s' % default_password)

    computer_name = __salt__['system.get_computer_name']()

    user_list = __salt__['user.list_users']()
    log.info('user list:' + str(user_list))
    # if default_user not in user_list:
    #     result = _set_winlogon_key('AutoAdminLogon', '0')
    #     ret['result'] = False
    #     ret['comment'] = '%s is not exist' % default_user
    #     return ret

    # auto admin logon key
    # not exist, the create key module will set key instead fo create key
    # if a key is already exist
    keys = [('AutoAdminLogon', '1'),
            ('DefaultUserName', username),
            ('DefaultDomainName', computer_name),
            ('DefaultPassword', password)]

    try:
        for key in keys:
            result = _set_winlogon_key(key[0], key[1])
            log.info(str(key[0]) + ': ' + str(result))

    except Exception as err:
        ret['result'] = False
        ret['comment'] = str(err)
        return ret

    ret['changes'] = {
        'old': 'auto logon for user:%s is not set' % username,
        'new': 'auto logon for user:%s is set, need to reboot system' % username,
    }

    ret['result'] = True
    ret['comment'] = 'auto logon for user:%s is set, need to reboot system' % username

    return ret