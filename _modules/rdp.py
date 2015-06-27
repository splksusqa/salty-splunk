

def ensure_user_is_activated(username):
    '''
    print if user is not in active desktop session
    :param username:
    :return:
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    cmd = 'qwinsta'
    cmd_result = __salt__['cmd.run_all'](cmd)

    if cmd_result['retcode'] != 0:
        ret['result'] = False
        ret['comment'] = cmd_result['stderr'] + cmd_result['stdout']
        return ret

    lines = cmd_result['stdout'].splitlines()
