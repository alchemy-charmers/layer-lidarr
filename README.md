# Overview

This charm provides [Lidarr](https://github.com/lidarr/Lidarr). Lidarr is an automatic NZB downloader for music.

# Usage

To deploy:

    juju deploy cs:~pirate-charmers/lidarr

This charm implements 
 * [interface:reverseproxy][interface-reverseproxy] intended for use with the 
   [HAProxy Charm][charm-haproxy]. This should be used if remote access is required 
   to enable TLS encryption. 
 * [interface:usenetdownloader][interface-usenetdownloader] intended for use
   with the [Sabnzbd Charm][charm-sabnzbd].  

## Known Limitations and Issues

This charm is under development, several other use cases/features are still under
consideration. Merge requests are certainly appreciated, some examples of
current limitations include.

 * Scale out usage is not intended, I'm not even sure what use it would be
 * The GitHub API is used to find the latest release, and if the install hook runs too many time, you could find
   yourself hitting an API limit will cause the hook to fail

# Configuration
You will most likely want to use a bundle to set options during deployment. 

See the full list of configuration options below. This will detail some of the
options that are worth highlighting.

 - restore-config: Combined with a resource allows restoring a previous
   configuration. This can also be used to migrate from non-charmed
   Lidarr. The Lidarr backup zip needs to be attached as the resource Lidarrconfig. 
 - backup-count: This configuration is not currently used.
 - backup-location: A folder to sync the Lidarr backups to daily, number and
   frequency of backups are controlled by Lidarr . This charm simply syncs
   (including deletions) the Backup folder to another location of your choosing.
 - proxy-*: The proxy settings allow configuration of the reverseproxy interface
   that will be registered during relation.
 - hostname will allow you to customize the hostname, be aware that
   doing this can cause multiple hosts to have the same hostname if you scale
   out the number of units. Setting hostname to "$UNIT" will set the hostname to
   the juju unit id. Note scaling out is not supported, tested, or useful.

# Contact Information

## Upstream Project Information

  - Code: https://github.com/pirate-charmers/layer-lidarr
  - Bug tracking: https://github.com/pirate-charmers/layer-lidarr/issues
  - Contact information: james@ec0.io

## Related links

[Lidarr](https://github.com/lidarr/Lidarr)
[charm-haproxy](https://jujucharms.com/u/pirate-charmers/haproxy)
[charm-sabnzbd](https://jujucharms.com/u/pirate-charmers/sabnzbd)
[interface-reverseproxy](https://github.com/pirate-charmers/interface-reverseproxy)
[interface-usenetdownloader](https://github.com/pirate-charmers/interface-usenet-downloader)

