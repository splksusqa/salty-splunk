
import subprocess

def _call_salt_module(name, args=None):
    subprocess.call(['sudo', 'salt-call', 'saltutil.sync_all'])
    script = ['sudo', 'salt-call', name]
    if args is not None:
        script = script + args

    p = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()

    if err:
        raise RuntimeError(err)

    return out


class TestSplunk():

    def test_download(self):
        out = _call_salt_module('splunk.download', 'test')
        assert 'test' in out
