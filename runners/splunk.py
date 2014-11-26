__author__ = 'cchung'

# Import salt modules
import salt.client

def event_count(expected=0):
    client = salt.client.LocalClient(__opts__['conf_file'])
    counts = client.cmd('*', 'splunk.total_event_count', ['_internal'])
    total = 0
    for c in counts.values():
        total += c
    assert total >= expected


def up():
    '''
    Print a list of all of the minions that are up
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
    minions = client.cmd('*', 'test.ping', timeout=1)
    for minion in sorted(minions):
        print minion