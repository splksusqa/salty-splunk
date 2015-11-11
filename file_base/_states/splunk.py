def installed(name, **kwargs):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    if __salt__['splunk.is_installed']():
        ret['comment'] = 'Splunk is already installed.'
        return ret

    result = __salt__['splunk.install'](**kwargs)
    if result:
        ret['changes'] = {
            'old': 'No splunk installed',
            'new': result
        }
        ret['comment'] = "Splunk is installed"
    return ret
