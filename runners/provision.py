import os
import re
import time
import salt

ROLES = ['idx', 'sh', 'fwd', 'lic', 'dmc', 'dep']

class SaltWrapper(object):

    def __init__(self, roles, tag, log='', conf_dir=''):
        self.roles = roles
        self.groups = {
            'idx': {
                'master': 'splunk-cluster-master',
                'slave': 'splunk-cluster-slave',
                'standalone': 'splunk-indexer'},
            'sh': {
                'idx-cluster': 'splunk-cluster-searchhead',
                'shc-captain': 'splunk-shc-captain',
                'shc-member': 'splunk-shc-member',
                'standalone': 'splunk-searchhead'},
            'fwd': {
                'universal': 'splunk-universal-fwd',
                'heavy': 'splunk-heavy-fwd',
                'light': 'splunk-light-fwd'},
            'lic': 'splunk-lic-master',
            'dmc': 'splunk-dmc',
            'dep': 'splunk-deployer'
        }

        self.tag = tag or 'no_tag'
        self.conf_dir = conf_dir or '/etc/salt/'
        self.salt_home = '/srv/salt'
        self.pillars = {
            'top': os.path.join(self.salt_home, 'pillar', 'top.sls'),
            'splunk': {
                'common': os.path.join(self.salt_home, 'pillar', 'splunk',
                                       'common.sls'),
            }
        }
        self.log_file = os.path.join(os.path.expanduser('~'),
                                     log or 'provision.log')
        self.salt_log = os.path.join(os.path.expanduser('~'), 'salt_log')
        self.conf = {'master': os.path.join(self.conf_dir, 'master'),
                     'minion': os.path.join(self.conf_dir, 'minion'),
                     'cloud' : os.path.join(self.conf_dir, 'cloud')}
        self.machines = self.get_machine_list()
        self.machines_num = sum([len(self.machines[i]) for i in self.machines])
        self.master = salt.client.LocalClient(self.conf['master'])
        self.master_opts = salt.config.master_config('/etc/salt/master')
        self.runner = salt.runner.RunnerClient(self.master_opts)
        print self.roles


    def get_machine_list(self):
        machines = {}
        profile = "{platform}-{role}-{size}"

        if self.roles['idx']['cluster']:
            self.roles['idx']['role'] = self.groups['idx']['master']
            master_prof = profile.format(**self.roles['idx'])
            master = [self.tag + '-' + master_prof]
            machines.update({master_prof: master})
            self.roles['idx']['role'] = self.groups['idx']['slave']
        else:
            self.roles['idx']['role'] = self.groups['idx']['standalone']

        if self.roles['sh']['cluster']:
            self.roles['sh']['role'] = self.groups['sh']['shc-captain']
            captain_prof = profile.format(**self.roles['sh'])
            captain = [self.tag + '-' + captain_prof]
            machines.update({captain_prof: captain})
            self.roles['sh']['role'] = self.groups['sh']['shc-member']
        elif self.roles['idx']['cluster']:
            self.roles['sh']['role'] = self.groups['sh']['idx-cluster']
        else:
            self.roles['sh']['role'] = self.groups['sh']['standalone']

        self.roles['lic']['role'] = self.groups['lic']
        self.roles['dmc']['role'] = self.groups['dmc']
        self.roles['dep']['role'] = self.groups['dep']

        for r in ROLES:
            if not isinstance(self.roles[r]['num'], int):
                self.roles[r]['num'] = 1 if self.roles[r]['num'] else 0
            print self.roles[r]
            prof = profile.format(**self.roles[r])
            names = [self.tag + '-' + prof + '-' + str(i)
                     for i in range(self.roles[r]['num'])]
            machines.update({prof:names})
        return machines


    def launch_all(self, parallel=True):
        for profile, names in self.machines.iteritems():
            if len(names):
                print "Launching {}".format(names)
            cloud = salt.cloud.CloudClient(self.conf['cloud'])
            cloud.profile(profile, names, parallel=parallel)

        start = time.time()
        timeout = 900 # 15 mins
        while True:
            time.sleep(30)
            all_machines = self.runner.cmd('manage.status', [])
            connected = all_machines['up']
            waiting = all_machines['down']
            if len(connected) == self.machines_num:
                print "All machines are up!"
                break
            elif time.time() - start > timeout:
                print "Time out after {}s!".format(time.time() - start)
            else:
                print "Connected: {}".format(connected)
                print "Waiting for: {}".format(waiting)

        self.master.cmd('*', 'saltutil.sync_all', [])
        self.master.cmd('*', 'saltutil.refresh_pillar', [])
        return 0


    def setup_all(self):
        for r, values in self.roles.iteritems():
            self.generate_pillar(values['version'], values['build'],
                                 values['role'])
        return self.runner.cmd('state.orch', ['orchestration.all'])


    def generate_pillar(self, version, build, role):
        pillar_dest = os.path.join(self.salt_home,'pillar','splunk',role+'.sls')
        base_role = "{r}':\n    - match: grain\n    - splunk.{r}".format(r=role)
        with open(self.pillars['splunk']['common'], 'r+') as of:
            with open(pillar_dest, 'w+') as df:
                for l in of.readlines():
                    if '  version:' in l:
                        df.write(re.sub(r'  version:.*',
                                        "  version: {}".format(version), l))
                    elif '  build:' in l:
                        df.write(re.sub(r'  build:.*',
                                        "  build: {}".format(build), l))
                    else:
                        df.write(l)
        top = open(self.pillars['top'], 'r+')
        text = top.read()
        top.seek(0)
        top.write(re.sub(
            r"{}':\n    - match: grain\n    - splunk\.common.*".format(role),
            base_role, text))
        top.truncate()
        top.close()


def provision(tag='no_tag', log='provision.log', **kwargs):
    roles = {}
    for r in ROLES:
        roles.update({r: kwargs.get(r, {})})
    s = SaltWrapper(roles, tag, log)
    s.launch_all()
    s.setup_all()
    return 0
