import os
from util import run_cmd, get_version
from util import MethodMissing
from exceptions import CommandExecutionError
import logging
import json


logger = logging.getLogger(__name__)


def get_splunk(splunk_home, username="admin", password="changeme",
               scheme='https', login=True):
    '''
    get splunk object by splunk version
    '''
    version = get_version(splunk_home)

    if version[0] == 6 and version[1] == 2:
        return SplunkDash(splunk_home, username, password, scheme, login)
    elif version[0] == 6 and version[1] >= 5:
        return SplunkIvory(splunk_home, username, password, scheme, login)
    elif version[0] == 7 and version[1] >= 1:
        return SplunkNightlight(
            splunk_home, username, password, scheme, login)
    elif version[0] == 7:
        return SplunkIvory(splunk_home, username, password, scheme, login)
    else:
        return SplunkNightlight(
            splunk_home, username, password, scheme, login)


class Splunk(MethodMissing):
    '''
    This class represents a splunk instance
    '''
    def __init__(self, splunk_home, username="admin", password="changeme",
                 scheme='https', login=True):
        '''
        :param host: The host name (the default is "localhost").
        :type host: ``string``
        :param port: The port number (the default is 8089).
        :type port: ``integer``
        :param scheme: The scheme for accessing the service (the default is
                       "https").
        :type scheme: "https" or "http"
        :type username: ``string``
        :param `password`: The password for the Splunk account.
        :type password: ``string``
        '''
        self.splunk_home = splunk_home
        self.username = username
        self.password = password
        self.scheme = scheme

        if login:
            self.login()

    def method_missing(self, name):
        if hasattr(self.splunk, name):
            return getattr(self.splunk, name)
        else:
            raise AttributeError(
                "Splunk does not respond to {n}".format(n=name))

    @property
    def is_ftr(self):
        '''
        check if the splunk is first time run
        '''
        return os.path.exists(os.path.join(self.splunk_home, 'ftr'))

    def login(self):
        '''
        get splunk instance
        '''
        try:
            from splunklib import client
        except ImportError:
            __salt__['pip.install']('splunk-sdk')
            from splunklib import client

        self.splunk = client.connect(
            username=self.username, password=self.password, scheme=self.scheme,
            autologin=True)

    def cli(self, cli, auth="admin:changeme"):
        '''
        run cli
        '''
        execute = os.path.join(self.splunk_home, 'bin', 'splunk')
        if auth is None:
            cmd = '"{e}" {c}'.format(e=execute, c=cli)
        else:
            cmd = '"{e}" {c} -auth {a}'.format(e=execute, c=cli, a=auth)
        return run_cmd(cmd)

    def is_running(self):
        '''
        return splunk is running or not
        '''
        result = self.cli("status", auth=None)
        return 'pid' in result['stdout'].lower()

    def start(self):
        '''
        start splunk via cli
        '''
        cmd = "start --accept-license --answer-yes"
        if self.is_ftr:
            result = self.cli("enable boot-start", anth=None)
            if result['retcode'] != 0:
                return result['retcode']

        result = self.cli(cmd, auth=None)
        return result['retcode']

    def stop(self):
        '''
        stop splunk via cli
        '''
        result = self.cli("stop", auth=None)
        return result['retcode']

    def restart(self, interface='cli'):
        '''
        restart splunk
        '''
        if 'cli' == interface:
            return self.cli('restart', auth=None)
        elif 'rest' == interface:
            return self.splunk.restart()
        else:
            return self.cli('restart', auth=None)

    def change_namespace(self, owner, app, sharing):
        '''
        '''
        try:
            from splunklib import client
        except ImportError:
            __salt__['pip.install']('splunk-sdk')
            from splunklib import client

        self.splunk = client.connect(
            username=self.username, password=self.password, owner=owner,
            app=app, sharing=sharing, autologin=True)

    def allow_remote_login(self):
        '''
        config allowRemoteLogin under server.conf
        '''
        self.edit_conf_file(
            'server', 'general', {'allowRemoteLogin': 'always'},
            app='nobody', owner='nobody', sharing='system')

    def enable_js_debug_mode(self):
        '''
        by disabling js cache and minify js, javascript could be debugged
        by browser console
        '''
        self.edit_conf_file(
            'web', 'settings', {'js_no_cache': True, 'minify_js': False},
            app='nobody', owner='nobody', sharing='system')

    @property
    def mgmt_port(self):
        '''
        get mgmt uri of splunk

        :return: The mgmt uri of splunk, return None if Splunk is not started
        :rtype: string
        '''
        # todo auth parameter

        cli_result = self.cli("show splunkd-port")

        if 0 == cli_result['retcode']:
            port = cli_result['stdout'].replace("Splunkd port: ", "").strip()
            return port
        else:
            return None

    @property
    def server_name(self):
        '''
        get server name of this splunk instance
        :return: The server name of this instance
        :rtype: string
        '''
        return self.read_conf_file('server', 'general', 'serverName')

    @property
    def mgmt_uri(self):
        '''
        get the mgmt uri of this splunk instance
        :return: the management uri of this instance
        :rtype: string
        '''
        return "{scheme}://{s}:{p}".format(
            scheme=self.scheme, s=self.server_name, p=self.mgmt_port)

    def add_license(self, path):
        '''
        add license to splunk
        :param path: path to the license file
        '''
        result = self.cli("add license {p}".format(p=path))

        if 0 == result['retcode']:
            return self.restart()
        else:
            return result

    def remove_search_peer(self, peers):
        '''
        remove search peer from a search head
        :type servers: list
        :param servers: ex, ['<ip>:<port>','<ip>:<port>', ...]
        '''
        # try to remove servers not in list
        # todo fix username and password
        if type(peers) is not list:
            peers = [peers, ]

        for peer in peers:
            result = self.cli('remove search-server -url {h}'.format(h=peer))
            if result['retcode'] != 0:
                raise CommandExecutionError(
                    result['stderr'] + result['stdout'])

    def edit_conf_file(
            self, conf_name, stanza_name, data=None, app=None,
            owner=None, sharing='system', do_restart=True):
        """
        config conf file by REST, if a data is existed, it will skip

        :param conf_name: name of config file
        :param stanza_name: stanza need to config
        :param data: data under stanza
        :param do_restart: restart after configuration
        :param app: namespace of the conf
        :param owner: namespace of the conf
        :param sharing: The scope you want the conf to be. it can be user,
                        app, or system.
        :return: no return value
        :raise EnvironmentError: if restart fail
        """
        from splunklib.binding import HTTPError

        self.change_namespace(app=app, owner=owner, sharing=sharing)
        conf = self.splunk.confs[conf_name]

        data = dict() if data is None else data

        try:
            stanza = conf[stanza_name]
        except KeyError:
            conf.create(stanza_name)
            stanza = conf[stanza_name]
        except HTTPError as err:
            logger.critical('%s is existed' % str(stanza_name))
            logger.debug(err)

        stanza.submit(data)

        if do_restart:
            self.restart()

    def read_conf_file(
            self, conf_name, stanza_name=None, key_name=None, owner=None,
            app=None, sharing='system'):
        """
        read config file

        :param conf_name: name of config file
        :param stanza_name: stanza need to config
        :param key_name: key for the value you want to read
        :param owner: namespace of the conf
        :param app: namespace of the conf
        :param sharing: The scope you want the conf to be. it can be
            user, app, or system.
        :return: if no key_name, stanza content will be returned, else will be
            value of given stanza and key_name
        """
        self.change_namespace(app=app, owner=owner, sharing=sharing)

        try:
            conf = self.splunk.confs[conf_name]
            if stanza_name is None:
                return conf
        except KeyError:
            logger.warn("no such conf file %s" % conf_name)
            return None

        try:
            stanza = conf[stanza_name]
            if key_name is None:
                return stanza.content
        except KeyError:
            logger.warn('no such stanza, %s' % stanza_name)
            return None

        if key_name not in stanza.content:
            logger.warn('no such key name, %s' % key_name)
            return None

        return stanza[key_name]

    def is_stanza_existed(
            self, conf_name, stanza_name, owner=None, app=None,
            sharing='system'):
        '''
        check if a stanza is existed in the given conf file

        :type conf_name: string
        :type stanza_name: string
        :type sharing: string
        :param conf_name: name of the conf file
        :param stanza_name: name of the stanza to check
        :param owner: namespace of the conf
        :param app: namespace of the conf
        :param sharing: The scope you want the conf to be. it can be user, app,
                        or system.
        :return: boolean
        '''
        self.change_namespace(owner=owner, app=app, sharing=sharing)

        try:
            conf = self.splunk.confs[conf_name]
        except KeyError:
            logger.warn("no such conf file %s" % conf_name)
            return None
        return stanza_name in conf

    def config_cluster_master(
            self, pass4SymmKey, cluster_label, replication_factor=2,
            search_factor=2, number_of_sites=1,
            site_replication_factor="origin:2,total:3",
            site_search_factor="origin:2,total:3"):
        """
        config splunk as a master of a indexer cluster

        :param pass4SymmKey: it's a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param search_factor: factor of bucket be able to search
        :param replication_factor: factor of bucket be able to replicate
        :param number_of_sites: number of sites of the cluster
        :param site_replication_factor: site replication factor for the cluster
        :param site_search_factor: site search factor of the cluster
        """
        def get_availaible_sites():
            return ', '.join(
                ["site" + str(i) for i in range(1, number_of_sites+1)])

        if number_of_sites > 1:
            # multi-site
            self.edit_conf_file(
                'server', 'general', {'site': 'site1'}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')

            data = {'pass4SymmKey': pass4SymmKey,
                    'mode': 'master',
                    'multisite': True,
                    'available_sites': get_availaible_sites(),
                    'site_replication_factor': site_replication_factor,
                    'site_search_factor': site_search_factor}
        else:
            # single-site
            data = {'pass4SymmKey': pass4SymmKey,
                    'replication_factor': replication_factor,
                    'search_factor': search_factor,
                    'mode': 'master'}

        if cluster_label is not None:
            data['cluster_label'] = cluster_label

        self.edit_conf_file('server', 'clustering', data,
            app='nobody', owner='nobody', sharing='system')

    def is_cluster_master(self):
        '''
        check if this instance is a cluster master or not
        '''
        self.change_namespace('nobody', 'nobody', 'system')
        mode = self.read_conf_file(
            'server', 'clustering', 'mode',
            app='nobody', owner='nobody', sharing='system')
        return 'master' == mode

    def is_shc_deployer(self):
        '''
        check if this instance is a shc deployer or not
        '''
        self.change_namespace('nobody', 'nobody', 'system')
        content = self.read_conf_file('server', 'shclustering')
        return content is not None and 'conf_deploy_fetch_url' not in content

    def is_license_master(self):
        '''
        check if this instance is a license master
        '''
        self.change_namespace('nobody', 'nobody', 'system')
        master_uri = self.read_conf_file('server', 'license', 'master_uri')
        return 'self' == master_uri

    def is_deployment_server(self):
        '''
        check if this instance is a deployment server
        '''
        self.change_namespace('nobody', 'nobody', 'system')
        content = self.read_conf_file('serverclass')
        return len(content) > 1

    def config_cluster_slave(
            self, pass4SymmKey, cluster_label, master_uri,
            replication_port=9887, site=None):
        """
        config splunk as a peer(indexer) of a indexer cluster

        :param pass4SymmKey: is a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param replication_port: port to replicate data
        :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
            if not specified, will search minion under same master with role
            indexer-cluster-master
        :param site: None if the slave is on single site, else "site1"
                     or "site2"...
        :type site: string
        """
        if not master_uri.startswith('http'):
            master_uri = 'https://{u}'.format(u=master_uri)

        self.edit_conf_file(
            'server', "replication_port://{p}".format(p=replication_port),
            app='nobody', owner='nobody', sharing='system', do_restart=False)

        data = {'pass4SymmKey': pass4SymmKey,
                'master_uri': master_uri,
                'mode': 'slave'}

        if cluster_label is not None:
            data['cluster_label'] = cluster_label

        if site is not None:  # for multi-site
            self.edit_conf_file(
                'server', 'general', {'site': site},
                app='nobody', owner='nobody', sharing='system',
                do_restart=False)

        self.edit_conf_file(
            'server', 'clustering', data, app='nobody', owner='nobody',
            sharing='system')

    def config_cluster_searchhead(
            self, pass4SymmKey, cluster_label, master_uri, site=None):
        """
        config splunk as a search head of a indexer cluster
        http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Enableclustersindetail

        :param pass4SymmKey:  is a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
            if not specified, will search minion under same master with role
            splunk-cluster-master
        :param site: None if the search head is on single site, else
            "site1" or "site2"...
        :type site: string
        """
        if not master_uri.startswith('http'):
            master_uri = 'https://{u}'.format(u=master_uri)

        data = {'pass4SymmKey': pass4SymmKey,
                'master_uri': master_uri,
                'mode': 'searchhead'}

        if cluster_label is not None:
            data['cluster_label'] = cluster_label

        if site is not None:  # for multi-site
            self.edit_conf_file(
                'server', 'general', {'site': site}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
            data['multisite'] = True

        self.edit_conf_file(
            'server', 'clustering', data,
            app='nobody', owner='nobody', sharing='system')

    def config_shcluster_deployer(self, pass4SymmKey, shcluster_label):
        '''
        config a splunk as a deployer of a search head cluster

        :param shcluster_label: label for the shc
        :param pass4SymmKey: is a key to communicate between cluster
        '''
        data = {'pass4SymmKey': pass4SymmKey,
                'shcluster_label': shcluster_label}

        self.edit_conf_file(
            'server', 'shclustering', data=data,
            app='nobody', owner='nobody', sharing='system')

    def config_shcluster_member(
            self, pass4SymmKey, shcluster_label, replication_port,
            conf_deploy_fetch_url, replication_factor=None):
        '''
        config splunk as a member of a search head cluster

        :param pass4SymmKey: pass4SymmKey for SHC
        :param shcluster_label: shcluster's label
        :param replication_port: replication port for SHC
        :param replication_factor: replication factor for SHC,
            if it's None use default provided by Splunk
        :param conf_deploy_fetch_url: deployer's mgmt uri
        '''
        if not conf_deploy_fetch_url.startswith("https://"):
            conf_deploy_fetch_url = 'https://{u}'.format(
                u=conf_deploy_fetch_url)

        replication_factor_str = ''
        if replication_factor:
            replication_factor_str = '-replication_factor {n}'.format(
                n=replication_factor)

        cmd = 'init shcluster-config -mgmt_uri {mgmt_uri} ' \
              '-replication_port {replication_port} ' \
              '{replication_factor_str} ' \
              '-conf_deploy_fetch_url {conf_deploy_fetch_url} ' \
              '-secret {security_key} -shcluster_label {label}' \
              .format(
                    mgmt_uri=self.mgmt_uri,
                    replication_port=replication_port,
                    replication_factor_str=replication_factor_str,
                    conf_deploy_fetch_url=conf_deploy_fetch_url,
                    security_key=pass4SymmKey,
                    label=shcluster_label)

        result = self.cli(cmd)
        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

        result = self.restart()
        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

    def bootstrap_shcluster_captain(self, shc_members):
        '''
        bootstrap a splunk instance as a captain of a search head cluster
        captain

        :param servers_list: list of shc members,
            ex. https://192.168.0.2:8089,https://192.168.0.3:8089
        '''
        servers_list = ','.join(shc_members)

        cmd = 'bootstrap shcluster-captain -servers_list {s} '.format(
            s=servers_list)

        result = self.cli(cmd)

        if 0 != result['retcode']:
            raise CommandExecutionError("Error bootstraping shc captain")

        return result

    def config_search_peer(
            self, peers, remote_username='admin', remote_password='changeme'):
        '''
        config splunk as a peer of a distributed search environment

        if a search head is part of indexer cluster search head,
        will raise EnvironmentError

        :param peers: list value, ex, ['<ip>:<port>','<ip>:<port>']
        :param remote_username: splunk username of the search peer
        :param remote_password: splunk password of the search peer
        :raise CommandExecutionError, if failed
        '''
        if type(peers) is not list:
            peers = [peers, ]

        for peer in peers:
            cmd = ('add search-server -host {h} -remoteUsername {u} '
                   '-remotePassword {p}'.format(
                    h=peer, p=remote_password, u=remote_username))
            result = self.cli(cmd)

            if result['retcode'] != 0:
                raise CommandExecutionError(
                    result['stderr'] + result['stdout'])

    def config_deployment_client(self, server):
        '''
        config deploymeny client

        deployment client is not compatible if a splunk is
        :param server: mgmt uri of deployment server
        '''
        cmd = 'set deploy-poll {s}'.format(s=server)
        cli_result = self.cli(cmd)
        if cli_result['retcode'] != 0:
            raise CommandExecutionError(str(cli_result))

        restart_result = self.restart()
        if restart_result['retcode'] != 0:
            raise CommandExecutionError(str(restart_result))

    def config_license_slave(self, master_uri):
        '''
        config splunk as a license slave

        :param master_uri: uri of the license master
        :type master_uri: string
        '''
        self.edit_conf_file(
            'server', 'license', {'master_uri': master_uri},
            app='nobody', owner='nobody', sharing='system')

    def create_users(self, count, prefix='user', roles=['user']):
        '''
        create a batch of users
        '''
        if not isinstance(roles, list):
            roles = [roles, ]

        for i in range(count):
            user = prefix + str(i)
            self.splunk.users.create(username=user, password=user, roles=roles)

    def create_saved_searches(self, count, search, prefix='search', **kwargs):
        '''
        create a batch of saved searches
        '''
        for i in range(count):
            name = prefix + str(i)
            self.splunk.saved_searches.create(
                name=name, search=search, **kwargs)

    def enable_listen(self, port):
        '''
        enable listening on the splunk instance
        :param port: the port number to enable listening
        :type port: integer
        :return: None
        '''
        result = self.cli("enable listen {p}".format(p=port))

        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

    def add_forward_server(self, server):
        '''
        add forward server to the splunk instance
        :param server: server to add to the splunk instance
        :type server: string
        :return: None
        '''
        result = self.cli("add forward-server {s}".format(s=server))

        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

    def add_deployment_app(self, name):
        '''
        add an deployment app by making a new dierctory in
        $SPLUNK_HOME/etc/deployment-apps
        '''
        cmd = 'mkdir {p}'.format(
            p=os.path.join(self.splunk_home, 'etc', 'deployment-apps', name))
        result = run_cmd(cmd)

        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

    def get_listening_ports(self):
        '''
        get listening ports
        '''
        self.change_namespace('nobody', 'search', 'app')
        resp = self.get('data/inputs/tcp/cooked', output_mode='json').body
        resp = json.loads(resp.readall())
        return [entry['name'] for entry in resp['entry']]

    def config_dmc(
            self, searchheads, deployer, indexers,
            cluster_master, license_master, deployment_server, cluster_label,
            shcluster_label, app_name="splunk_management_console"):
        '''
        configure dmc
        '''
        self.change_namespace('nobody', 'nobody', 'system')

        if self.is_cluster_master():
            self.config_search_peer(searchheads + deployer)
        else:
            self.config_search_peer(searchheads + deployer + indexers)

        if not self.is_license_master():
            self.config_search_peer(license_master)

        if not self.is_deployment_server():
            self.config_search_peer(deployment_server)

        # set distsearch groups by editing distsearch.conf
        # indexer
        self.edit_conf_file(
            'distsearch', 'distributedSearch:dmc_group_indexer',
            {'servers': ','.join(indexers), 'default': True}, do_restart=False,
            app='nobody', owner='nobody', sharing='system')

        # search head
        self.edit_conf_file(
            'distsearch', 'distributedSearch:dmc_group_search_head',
            {'servers': ','.join(searchheads)}, do_restart=False,
            app='nobody', owner='nobody', sharing='system')

        # kv store
        self.edit_conf_file(
            'distsearch', 'distributedSearch:dmc_group_kv_store',
            {'servers': ','.join(searchheads)}, do_restart=False,
            app='nobody', owner='nobody', sharing='system')

        # license master
        if self.is_license_master():
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_license_master',
                {'servers': 'localhost:localhost'}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        elif len(license_master) > 0:
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_license_master',
                {'servers': ','.join(license_master)}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        else:
            pass

        # cluster master
        if self.is_cluster_master():
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_cluster_master',
                {'servers': 'localhost:localhost'}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        elif len(cluster_master) > 0:
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_cluster_master',
                {'servers': ','.join(cluster_master)}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        else:
            pass

        # deployment server
        if self.is_deployment_server():
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_deployment_server',
                {'servers': 'localhost:localhost'}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        elif len(deployment_server) > 0:
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_deployment_server',
                {'servers': ','.join(deployment_server)}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        else:
            pass

        # shc deployer
        if self.is_shc_deployer():
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_deployment_server',
                {'servers': 'localhost:localhost'}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        elif len(deployer) > 0:
            self.edit_conf_file(
                'distsearch', 'distributedSearch:dmc_group_deployment_server',
                {'servers': ','.join(deployer)}, do_restart=False,
                app='nobody', owner='nobody', sharing='system')
        else:
            pass

        # we should do following 2 steps only after ember
        if len(cluster_master) > 0:
            stanza = 'distributedSearch:dmc_indexerclustergroup_{l}'.format(
                l=cluster_label)

            self.edit_conf_file(
                'distsearch', stanza,
                {"servers": ",".join(indexers + searchheads)},
                do_restart=False, app='nobody', owner='nobody',
                sharing='system')

        # config shcluster group if shcluster is enabled
        if len(deployer) > 0:
            stanza = 'distributedSearch:dmc_searchheadclustergroup_{l}'.format(
                l=shcluster_label)

            self.edit_conf_file(
                'distsearch', stanza,
                {"servers": ",".join(searchheads + deployer)},
                do_restart=False, app='nobody', owner='nobody',
                sharing='system')

        # configure app.conf
        self.edit_conf_file(
            'app', 'install', {'is_configured': True}, owner="nobody",
            app=app_name, sharing="app", do_restart=False)

        # add all machines to splunk_management_console_assets.conf
        all_peers = indexers + searchheads + deployer + deployment_server + \
            license_master

        conf_name = app_name + "_assets"
        self.edit_conf_file(
            conf_name, 'settings',
            {'configuredPeers': ','.join(all_peers)},
            app=app_name, owner="nobody", sharing="app", do_restart=True)

        # Run the "DMC Asset - Build Full" saved search
        self.change_namespace("nobody", app_name, "app")
        self.splunk.post(
            'saved/searches/DMC Asset - Build Full/dispatch',
            trigger_actions=1)


    def is_dmc_configured(self, app_name='splunk_management_console'):
        configured = self.read_conf_file(
            conf_name='app', stanza_name='install', key_name='is_configured',
            owner='nobody', app=app_name, sharing='app')

        if "0" == configured or configured is None:
            return False
        else:
            return True


class SplunkDash(Splunk):
    '''
    6.2 version of Splunk instance
    '''
    def config_cluster_searchhead(
            self, pass4SymmKey, master_uri, cluster_label=None, site=None):
        """
        config splunk as a search head of a indexer cluster
        http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Enableclustersindetail

        :param pass4SymmKey:  is a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
            if not specified, will search minion under same master with role
            splunk-cluster-master
        :param site: None if the search head is on single site, else
            "site1" or "site2"...
        :type site: string
        """
        cluster_label = None

        super(SplunkDash, self).__init__(
            pass4SymmKey=pass4SymmKey, master_uri=master_uri,
            cluster_label=cluster_label, site=site)

    def config_cluster_master(
            self, pass4SymmKey, cluster_label=None, replication_factor=2,
            search_factor=2, number_of_sites=1,
            site_replication_factor="origin:2,total:3",
            site_search_factor="origin:2,total:3"):
        """
        config splunk as a master of a indexer cluster

        :param pass4SymmKey: it's a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param search_factor: factor of bucket be able to search
        :param replication_factor: factor of bucket be able to replicate
        :param number_of_sites: number of sites of the cluster
        :param site_replication_factor: site replication factor for the cluster
        :param site_search_factor: site search factor of the cluster
        """
        cluster_label = None

        super(SplunkDash, self).__init__(
            pass4SymmKey=pass4SymmKey, cluster_label=cluster_label,
            replication_factor=replication_factor, search_factor=search_factor,
            number_of_sites=number_of_sites,
            site_replication_factor=site_replication_factor,
            site_search_factor=site_search_factor)

    def config_cluster_slave(
            self, pass4SymmKey, master_uri, cluster_label=None,
            replication_port=9887, site=None):
        """
        config splunk as a peer(indexer) of a indexer cluster

        :param pass4SymmKey: is a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param replication_port: port to replicate data
        :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
            if not specified, will search minion under same master with role
            indexer-cluster-master
        :param site: None if the slave is on single site, else "site1"
                     or "site2"...
        :type site: string
        """
        cluster_label = None
        super(SplunkDash, self).__init__(
            pass4SymmKey=pass4SymmKey, master_uri=master_uri,
            cluster_label=cluster_label, replication_port=replication_port,
            site=site)


class SplunkIvory(Splunk):
    '''
    Version 6.5 (or up) of Splunk
    '''
    def config_dmc(
            self, searchheads, deployer, indexers,
            cluster_master, license_master, deployment_server, cluster_label,
            shcluster_label):
        '''
        configure dmc
        '''
        super(SplunkIvory, self).config_dmc(
            searchheads, deployer, indexers, cluster_master, license_master,
            deployment_server, cluster_label, shcluster_label,
            app_name='splunk_monitoring_console')

    def is_dmc_configured(self):
        '''
        check if dmc is configured
        '''
        return super(SplunkIvory, self).is_dmc_configured(
            app_name='splunk_monitoring_console')


class SplunkNightlight(SplunkIvory):
    '''
    Version 7.1 (or up) of Splunk
    '''
    def start(self):
        '''
        start splunk
        '''
        if self.is_ftr:
            # write user-seed.conf
            path = os.path.join(
                self.splunk_home, 'etc', 'system', 'local', 'user-seed.conf')
            content = "[user_info]\nUSERNAME = admin\nPASSWORD = changeme"
            with open(path, 'w') as conf:
                conf.write(content)

        return super(SplunkNightlight, self).start()
