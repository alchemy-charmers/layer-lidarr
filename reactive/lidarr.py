from charms.reactive import (
    when_all,
    when_not,
    set_state,
    hook
)

from charmhelpers.core import host
from charmhelpers.core import hookenv
from pathlib import Path
from zipfile import ZipFile
from lib_lidarr import LidarrHelper

import os
import time
import socket

lidarr = LidarrHelper()


@hook('upgrade-charm')
def handle_upgrade():
    if not lidarr.kv.get('mono-source'):
        lidarr.install_deps()


@when_all('layer-service-account.configured')
@when_not('lidarr.installed')
def install_lidarr():
    hookenv.status_set('maintenance', 'Installing Lidarr')
    if not lidarr.kv.get('mono-source'):
        lidarr.install_deps()
    lidarr.install_lidarr()
    hookenv.status_set('maintenance', 'Installed')
    set_state('lidarr.installed')


@when_all('lidarr.installed',
          'layer-service-account.configured',
          'layer-hostname.installed')
@when_not('lidarr.configured')
def setup_config():
    hookenv.status_set('maintenance', 'Configuring Lidarr')
    backups = './backups'
    if lidarr.charm_config['restore-config']:
        try:
            os.mkdir(backups)
        except OSError as e:
            if e.errno == 17:
                pass
        backupFile = hookenv.resource_get('lidarrconfig')
        if backupFile:
            with ZipFile(backupFile, 'r') as inFile:
                inFile.extractall(lidarr.config_dir)
            hookenv.log(
                "Restoring config, indexers are disabled enable with action when configuration has been checked", 'INFO'
            )
            # Turn off indexers
            lidarr.set_indexers(False)
        else:
            hookenv.log("Add lidarrconfig resource, see juju attach or disable restore-config", 'WARN')
            hookenv.status_set('blocked', 'waiting for lidarrconfig resource')
            return
    else:
        host.service_start(lidarr.service_name)
        configFile = Path(lidarr.config_file)
        while not configFile.is_file():
            time.sleep(1)
    lidarr.modify_config(port=lidarr.charm_config['port'], urlbase='None')
    hookenv.open_port(lidarr.charm_config['port'], 'TCP')
    host.service_start(lidarr.service_name)
    hookenv.status_set('active', 'Lidarr is ready')
    set_state('lidarr.configured')


@when_not('usenet-downloader.configured')
@when_all('usenet-downloader.triggered', 'usenet-downloader.available', 'lidarr.configured')
def configure_downloader(usenetdownloader, *args):
    hookenv.log(
        "Setting up sabnzbd relation requires editing the database and may not work",
        "WARNING")
    lidarr.setup_sabnzbd(port=usenetdownloader.port(),
                         apikey=usenetdownloader.apikey(),
                         hostname=usenetdownloader.hostname())
    usenetdownloader.configured()


@when_not('plex-info.configured')
@when_all('plex-info.triggered', 'plex-info.available', 'lidarr.configured')
def configure_plex(plexinfo, *args):
    hookenv.log("Setting up plex relation requires editing the database and may not work", "WARNING")
    lidarr.setup_plex(hostname=plexinfo.hostname(), port=plexinfo.port(),
                      user=plexinfo.user(), passwd=plexinfo.passwd())
    plexinfo.configured()


@when_all('reverseproxy.triggered', 'reverseproxy.ready')
@when_not('reverseproxy.configured', 'reverseproxy.departed')
def configure_reverseproxy(reverseproxy, *args):
    hookenv.log("Setting up reverseproxy", "INFO")
    proxy_info = {'urlbase': lidarr.charm_config['proxy-url'],
                  'subdomain': lidarr.charm_config['proxy-domain'],
                  'group_id': lidarr.charm_config['proxy-group'],
                  'external_port': lidarr.charm_config['proxy-port'],
                  'internal_host': socket.getfqdn(),
                  'internal_port': lidarr.charm_config['port']
                  }
    reverseproxy.configure(proxy_info)
    lidarr.modify_config(urlbase=lidarr.charm_config['proxy-url'])
    host.service_restart(lidarr.service_name)


@when_all('reverseproxy.triggered', 'reverseproxy.departed')
def remove_urlbase(reverseproxy, *args):
    hookenv.log("Removing reverseproxy configuration", "INFO")
    lidarr.modify_config(urlbase='None')
    host.service_restart(lidarr.service_name)
