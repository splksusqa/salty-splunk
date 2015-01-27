import os
import sys
import logging
from threading import Thread
import salt

ROLES = ['idx', 'sh', 'fwd', 'lic', 'dmc', 'dep']

class SaltWrapper(object):

    def __init__(self, roles, tag, log='', conf_dir=''):
        self.roles = roles
        self.groups = {
            'idx': ['splunk-cluster-master', 'splunk-cluster-slave',
                    'splunk-indexer'],
            'sh': ['splunk-cluster-searchhead', 'splunk-shc-member',
                   'splunk-searchhead'],
            'fwd': ['splunk-universal-fwd', 'splunk-heavy-fwd',
                    'splunk-light-fwd'],
            'lic': ['splunk-lic-master'],
            'dmc': ['splunk-dmc'],
            'dep': ['splunk-dep']
        }
        self.tag = tag or 'no_tag'
        self.conf_dir = conf_dir or '/etc/salt/'
        self.salt_home = '/srv/salt'
        self.log_file = os.path.join(os.path.expanduser('~'),
                                     log or 'provision.log')
        self.salt_log = os.path.join(os.path.expanduser('~'), 'salt_log')
        self.conf = {'master': os.path.join(self.conf_dir, 'master'),
                     'minion': os.path.join(self.conf_dir, 'minion'),
                     'cloud' : os.path.join(self.conf_dir, 'cloud')}
        self.machines = self.get_machine_list()
        self.master = salt.client.LocalClient(self.conf['master'])
        self.master_opts = salt.config.master_config('/etc/salt/master')
        self.runner = salt.runner.RunnerClient(self.master_opts)
        print self.__dict__

    def update_pillar_files(self):
        pass

    def get_machine_list(self):
        machines = {}
        profile = "{platform}-{role}-{size}"

        if self.roles['idx']['cluster']:
            self.roles['idx']['role'] = 'splunk-cluster-master'
            master_prof = profile.format(**self.roles['idx'])
            master = [self.tag + '-' + master_prof]
            machines.update({master_prof: master})
            self.roles['idx']['role'] = 'splunk-cluster-slave'
        else:
            self.roles['idx']['role'] = 'splunk-indexer'

        if self.roles['sh']['cluster']:
            self.roles['sh']['role'] = 'splunk-shc-captain'
            captain_prof = profile.format(**self.roles['sh'])
            captain = [self.tag + '-' + captain_prof]
            machines.update({captain_prof: captain})
            self.roles['sh']['role'] = 'splunk-shc-member'
        elif self.roles['idx']['cluster']:
            self.roles['sh']['role'] = 'splunk-cluster-searchhead'
        else:
            self.roles['sh']['role'] = 'splunk-searchhead'

        self.roles['lic']['role'] = 'splunk-lic-master'
        self.roles['dmc']['role'] = 'splunk-dmc'
        self.roles['dep']['role'] = 'splunk-deployer'

        for r in ROLES:
            if not isinstance(self.roles[r]['num'], int):
                self.roles[r]['num'] = 1 if self.roles[r]['num'] else 0
            print self.roles[r]
            prof = profile.format(**self.roles[r])
            names = [self.tag + '-' + prof + '-' + str(i)
                     for i in range(self.roles[r]['num'])]
            machines.update({prof:names})
        print machines
        return machines


    def launch_all(self, parallel=True):
        for profile, names in self.machines.iteritems():
            print profile, names
            cloud = salt.cloud.CloudClient(self.conf['cloud'])
            cloud.profile(profile, names, parallel=parallel)
        self.master.cmd('*', 'saltutil.sync_all', [])
        self.master.cmd('*', 'saltutil.refresh_pillar', [])
        return 0


def debug(tag='no_tag', log='provision.log', **kwargs):
    roles = {}
    for r in ROLES:
        roles.update({r: kwargs.get(r, {})})
    s = SaltWrapper(roles, tag, log)


def setup(tag='no_tag', log='provision.log', **kwargs):
    roles = {}
    for r in ROLES:
        roles.update({r: kwargs.get(r, {})})
    s = SaltWrapper(roles, tag, log)
    s.runner.cmd('state.orch', ['orchestration.all'])


def provision(tag='no_tag', log='provision.log', **kwargs):
    roles = {}
    for r in ROLES:
        roles.update({r: kwargs.get(r, {})})
    s = SaltWrapper(roles, tag, log)
    # parallel launching machines
    return s.launch_all()


# #!/bin/bash
# sudo salt-run provision.provision \
#     tag="${BUILD_TAG// /_}" \
#     log="$LOG_FILE" \
#     idx="{'num': $idx_num, 'version': \"$idx_version\", 'build': \"$idx_build\", 'platform': $idx_platform, 'apps': \"$idx_apps\", 'size': $idx_size, 'cluster': $idx_cluster}" \
#      sh="{'num': $sh_num,  'version': \"$sh_version \", 'build': \"$sh_build \", 'platform': $sh_platform , 'apps': \"$sh_apps \", 'size': $sh_size , 'cluster': $sh_cluster }" \
#     fwd="{'num': $fwd_num, 'version': \"$fwd_version\", 'build': \"$fwd_build\", 'platform': $fwd_platform, 'apps': \"$fwd_apps\", 'size': $fwd_size, 'role':    $fwd_type}" \
#     dmc="{'num': $dmc,     'version': \"$dmc_version\", 'build': \"$dmc_build\", 'platform': $dmc_platform, 'apps': \"$dmc_apps\", 'size': $dmc_size}" \
#     lic="{'num': $lic,     'version': \"$lic_version\", 'build': \"$lic_build\", 'platform': $lic_platform, 'apps': \"$lic_apps\", 'size': $lic_size', lic_file': $lic_file}" \
#     dep="{'num': $dep,     'version': \"$dep_version\", 'build': \"$dep_build\", 'platform': $dep_platform, 'apps': \"$dep_apps\", 'size': $dep_size}"
