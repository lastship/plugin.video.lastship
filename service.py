# -*- coding: utf-8 -*-
"""
    Lastship Add-on (C) 2020
    Credits to Placenta and Covenant; our thanks go to their creators

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Addon Name: Lastship
# Addon id: plugin.video.lastship
# Addon Provider: LastShip

from resources.lib.modules.tools import logger
from resources.lib.modules import control
import threading

control.execute('RunPlugin(plugin://%s)' % control.get_plugin_url({'action': 'service'}))


def syncTraktLibrary():
    control.execute(
        'RunPlugin(plugin://%s)' % 'plugin.video.lastship/?action=tvshowsToLibrarySilent&url=traktcollection')
    control.execute(
        'RunPlugin(plugin://%s)' % 'plugin.video.lastship/?action=moviesToLibrarySilent&url=traktcollection')


try:
    AddonVersion = control.addon('plugin.video.lastship').getAddonInfo('version')
    logger.info('######################### lastship ############################')
    logger.info('# lastship PLUGIN VERSION: %s' % str(AddonVersion))
    logger.info('###############################################################')
except Exception:
    logger.info('######################### lastship ############################')
    logger.info('# ERROR GETTING lastship VERSIONS - NO HELP WILL BE GIVEN AS THIS IS NOT AN OFFICIAL LASTSHIP INSTALL.')
    logger.info('###############################################################')

if control.setting('autoTraktOnStart') == 'true':
    syncTraktLibrary()

if int(control.setting('schedTraktTime')) > 0:
    logger.info('###############################################################')
    logger.info('#################### STARTING TRAKT SCHEDULING ################')
    logger.info('#################### SCHEDULED TIME FRAME ' + control.setting('schedTraktTime') + ' HOURS ################')
    timeout = 3600 * int(control.setting('schedTraktTime'))
    schedTrakt = threading.Timer(timeout, syncTraktLibrary)
    schedTrakt.start()
