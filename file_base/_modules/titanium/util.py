import subprocess
import os
import re


def run_cmd(cmd):
    '''
    run command with subprocess
    '''
    proc = subprocess.Popen(cmd, env=os.environ, shell=True,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.wait()
    stdout = "\n".join(proc.stdout.readlines())
    stderr = "\n".join(proc.stderr.readlines())
    return {"stdout": stdout, "stderr": stderr, 'retcode': proc.returncode}


def get_version(splunk_home):
    '''
    get splunk version by splunk home
    '''
    version_file = os.path.join(splunk_home, "etc", "splunk.version")
    with open(version_file, "r") as file:
        content = "".join(file.readlines())
        match = re.search("(?P<version>[\d\.]+)", content)
        version = [int(ver) for ver in match.group().split('.')]
    return version


class MethodMissing(object):
    def method_missing(self, name, *args, **kwargs):
        '''please implement'''
        raise NotImplementedError('please implement a "method_missing" method')

    def __getattr__(self, name):
        '''
        Returns a function def 'callable' that wraps method_missing
        '''
        if not hasattr(name, '__call__'):
            return self.method_missing(name)

        def callable(*args, **kwargs):
            '''
            Returns a method that will be calling an overloaded method_missing
            '''
            return self.method_missing(name, *args, **kwargs)
        return callable
