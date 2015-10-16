import salt.exceptions
import platform
import sys
import os
from distutils.version import StrictVersion

import ctypes


class OSVERSIONINFOEXW(ctypes.Structure):
    _fields_ = [('dwOSVersionInfoSize', ctypes.c_ulong),
                ('dwMajorVersion', ctypes.c_ulong),
                ('dwMinorVersion', ctypes.c_ulong),
                ('dwBuildNumber', ctypes.c_ulong),
                ('dwPlatformId', ctypes.c_ulong),
                ('szCSDVersion', ctypes.c_wchar * 128),
                ('wServicePackMajor', ctypes.c_ushort),
                ('wServicePackMinor', ctypes.c_ushort),
                ('wSuiteMask', ctypes.c_ushort),
                ('wProductType', ctypes.c_byte),
                ('wReserved', ctypes.c_byte)]


def get_os_version():
    """
    Get's the OS major and minor versions.  Returns a tuple of
    (OS_MAJOR, OS_MINOR).
    """
    os_version = OSVERSIONINFOEXW()
    os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
    retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
    if retcode != 0:
        raise Exception("Failed to get OS version")

    return str(os_version.dwMajorVersion) + '.' + str(os_version.dwMinorVersion)


windows_versions = {
    'Windows7': '6.1',
    'Windows8': '6.2',
    'Windows8.1': '6.3'
}

windows_server_versions = {
    'WindowsServer2003R2': '5.2',
    'WindowsServer2008': '6.0',
    'WindowsServer2008R2': '6.1',
    'WindowsServer2012': '6.2',
    'WindowsServer2012R2': '6.3'
}


def get_os_arch():
    if os.path.exists('C:\Program Files (x86)'):
        return 'x64'
    else:
        return 'x86'


def add_event(name, username, password, jenkins_master, jenkins_jar):
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    # jenkins slave label naming convention
    # windows + <version> + <minor version> + <arch> + <service pack>
    ver = StrictVersion(get_os_version())
    win_full_version = ''
    if 'Server' in platform.release():
        for key in windows_server_versions:
            if ver == StrictVersion(windows_server_versions[key]):
                win_full_version = key
    else:
        for key in windows_versions:
            if ver == StrictVersion(windows_versions[key]):
                win_full_version = key
    jenkins_labels = win_full_version + get_os_arch()
    jenkins_labels = str.lower(jenkins_labels)

    task_name = 'jenkins'
    jenkins_folder = 'c:\\jenkins'
    task_run_cmd = '"java -jar %s -executors 1 -master %s -labels %s -mode exclusive -fsroot %s"' % \
                   (jenkins_jar, jenkins_master, jenkins_labels, jenkins_folder)
    cmd = 'SCHTASKS /Create /SC ONLOGON /RL HIGHEST /IT /F /TN %s /TR %s /RU %s /RP %s ' % \
          (task_name, task_run_cmd, username, password)

    cmd_result = __salt__['cmd.run_all'](cmd)

    if cmd_result['retcode'] != 0:
        ret['result'] = False
        ret['comment'] = cmd_result['stderr'] + cmd_result['stdout']
        return ret

    ret['result'] = True
    ret['comment'] = cmd_result['stdout']
    return ret
