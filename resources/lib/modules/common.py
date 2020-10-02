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

import xbmcaddon, sys
addonID = 'plugin.video.lastship'
addon = xbmcaddon.Addon(addonID)
addonName = addon.getAddonInfo('name')
if sys.version_info[0] == 2:
    from xbmc import translatePath
    addonPath = translatePath(addon.getAddonInfo('path')).decode('utf-8')
    profilePath = translatePath(addon.getAddonInfo('profile')).decode('utf-8')
else:
    from xbmcvfs import translatePath
    addonPath = translatePath(addon.getAddonInfo('path'))
    profilePath = translatePath(addon.getAddonInfo('profile'))
