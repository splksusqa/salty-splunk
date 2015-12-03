import platform
import subprocess
import pip


def install_and_import_yaml():
    import importlib
    try:
        importlib.import_module('yaml')
    except ImportError:
        pip.main(['install', 'pyyaml'])
    finally:
        globals()['yaml'] = importlib.import_module('yaml')


def install_and_import_click():
    import importlib
    pkg = 'click'
    try:
        importlib.import_module(pkg)
    except ImportError:
        pip.main(['install', pkg])
    finally:
        globals()[pkg] = importlib.import_module(pkg)


install_and_import_yaml()
install_and_import_click()


@click.command()
@click.option('--kv', multiple=True, type=str)
def main(kv):
    windows_default_conf = "C:\\salt\\conf\\minion"
    linux_default_conf = '/etc/salt/minion'

    if 'windows' in platform.system().lower():
        conf = windows_default_conf
    else:
        conf = linux_default_conf

    with open(conf) as f:
        dct = yaml.load(f)

    if dct is None:
        dct = dict()

    for key_value in kv:
        arr = key_value.split('=', 1)
        key = str(arr[0])
        value = str(arr[1])
        dct[key] = value

    with open(conf, "w") as f:
        yaml.dump(dct, f, default_flow_style=False)

    windows_restart_minion_cmds = [
        ['net', 'stop', 'salt-minion'],
        ['timeout', '5'],
        ['net', 'start', 'salt-minion']
    ]
    unix_restart_minion = 'sudo service salt-minion restart'

    if 'windows' in platform.system().lower():
        for cmd in windows_restart_minion_cmds:
            subprocess.call(cmd, shell=True)
    else:
        subprocess.call(unix_restart_minion, shell=True)


if __name__ == '__main__':
    main()
