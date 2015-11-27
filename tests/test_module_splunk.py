
import subprocess
import os
import vagrant

def _call_salt_module(name, args=None):
    subprocess.call("C:/salt/salt-call.bat saltutil.sync_modules --local")
    script = ['C:/salt/salt-call.bat', name]
    if args is not None:
        script = script + args + ['--local']
    
    p = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    
    return out


class TestSplunk():

    def test_is_installed(self):
        out = _call_salt_module('splunk.is_installed')
        assert 'False' in out
