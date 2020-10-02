# -*- coding: UTF-8 -*-
"""
    Lastship Add-on (C) 2019
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

import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
try:
    from urllib import urlencode
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlencode, urlparse

PY2 = sys.version_info[0] == 2

integer = 1000

lang = xbmcaddon.Addon().getLocalizedString

lang2 = xbmc.getLocalizedString

setting = xbmcaddon.Addon().getSetting

setSetting = xbmcaddon.Addon().setSetting

addon = xbmcaddon.Addon

addItem = xbmcplugin.addDirectoryItem

item = xbmcgui.ListItem

directory = xbmcplugin.endOfDirectory

content = xbmcplugin.setContent

property = xbmcplugin.setProperty

addonInfo = xbmcaddon.Addon().getAddonInfo

infoLabel = xbmc.getInfoLabel

condVisibility = xbmc.getCondVisibility

jsonrpc = xbmc.executeJSONRPC

window = xbmcgui.Window(10000)

dialog = xbmcgui.Dialog()

progressDialog = xbmcgui.DialogProgress()

progressDialogBG = xbmcgui.DialogProgressBG()

windowDialog = xbmcgui.WindowDialog()

button = xbmcgui.ControlButton

image = xbmcgui.ControlImage

getCurrentDialogId = xbmcgui.getCurrentWindowDialogId()

keyboard = xbmc.Keyboard


# Modified `sleep` command that honors a user exit request
def sleep(time):
    while time > 0 and not xbmc.Monitor().abortRequested():
        xbmc.sleep(min(100, time))
        time = time - 100


execute = xbmc.executebuiltin

skin = xbmc.getSkinDir()

player = xbmc.Player()

playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

resolve = xbmcplugin.setResolvedUrl

openFile = xbmcvfs.File

makeFile = xbmcvfs.mkdir

deleteFile = xbmcvfs.delete

deleteDir = xbmcvfs.rmdir

listDir = xbmcvfs.listdir

transPath = xbmc.translatePath

skinPath = xbmc.translatePath('special://skin/')

addonPath = xbmc.translatePath(addonInfo('path'))

if PY2:
    dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')
else:
    dataPath = xbmc.translatePath(addonInfo('profile'))

settingsFile = os.path.join(dataPath, 'settings.xml')

viewsFile = os.path.join(dataPath, 'views.db')

bookmarksFile = os.path.join(dataPath, 'bookmarks.db')

providercacheFile = os.path.join(dataPath, 'providers.13.db')

metacacheFile = os.path.join(dataPath, 'meta.5.db')

searchFile = os.path.join(dataPath, 'search.1.db')

libcacheFile = os.path.join(dataPath, 'library.db')

cacheFile = os.path.join(dataPath, 'cache.db')


def autoTraktSubscription(tvshowtitle, year, imdb, tvdb):
    from resources.lib.modules import libtools
    libtools.libtvshows().add(tvshowtitle, year, imdb, tvdb)


def addonIcon():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'icon.png')
    return addonInfo('icon')


def addonThumb():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']):
        return os.path.join(art, 'poster.png')
    elif theme == '-':
        return 'DefaultFolder.png'
    return addonInfo('icon')


def addonPoster():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'poster.png')
    return 'DefaultVideo.png'


def addonBanner():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'banner.png')
    return 'DefaultVideo.png'


def addonFanart():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'fanart.jpg')
    return addonInfo('fanart')


def addonNext():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'next.png')
    return 'DefaultVideo.png'


def addonId():
    return addonInfo('id')


def addonName():
    return addonInfo('name')


def get_plugin_url(queries):
    try:
        query = urlencode(queries)
    except UnicodeEncodeError:
        for k in queries:
            if isinstance(queries[k], unicode):
                queries[k] = queries[k].encode('utf-8')
        query = urlencode(queries)
    addon_id = sys.argv[0]
    if not addon_id:
        addon_id = addonId()
    return addon_id + '?' + query


def artPath():
    theme = appearance()
    if theme in ['-', '']:
        return
    elif condVisibility('System.HasAddon(script.lastship.artwork)'):
        return os.path.join(xbmcaddon.Addon('script.lastship.artwork').getAddonInfo('path'), 'resources', 'media', theme)


def appearance():
    appearance = setting('appearance.1') if condVisibility('System.HasAddon(script.lastship.artwork)') else setting('appearance.alt')
    return appearance


def artwork():
    execute('RunPlugin(plugin://script.lastship.artwork)')


# Fanart
def select_fanart(arttype, imdb, count_tmdb, count_fanart):
    try:
        from resources.lib.modules import metacache
        # limit no. of poster to max. 20 need to do more
        if int(count_tmdb) > 20:
            count_tmdb = 20
        listitems = []
        liste = metacache.fetchfanartlist(imdb, arttype)

        for index, entry in enumerate(liste):
            listitem = xbmcgui.ListItem(str(entry))
            if index < int(count_tmdb):
                listitem.setLabel("Poster TMDb No. " + str(index)) if "poster" in arttype else listitem.setLabel("Background TMDb No. " + str(index))
            else:
                listitem.setLabel("Poster FanArt No. " + str(index - int(count_tmdb))) if "poster" in arttype else listitem.setLabel("Background FanArt No. " + str(index - int(count_tmdb)))
            listitem.setArt({'thumb': str(entry)})
            listitems.append(listitem)
        dbfanartid = xbmcgui.Dialog().select("FanArtSelect", listitems, useDetails=True)

        if not dbfanartid == -1:
            if dbfanartid < int(count_tmdb):
                metacache.setfanart(arttype, imdb, dbfanartid, "tmdb")
            else:
                dbfanartid = dbfanartid - int(count_tmdb)
                metacache.setfanart(arttype, imdb, dbfanartid, "fanart")

            refresh()
    except:
        return


def infoDialog(message, heading=addonInfo('name'), icon='', time=3000, sound=False):
    if icon == '':
        icon = addonIcon()
    elif icon == 'INFO':
        icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'WARNING':
        icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == 'ERROR':
        icon = xbmcgui.NOTIFICATION_ERROR
    dialog.notification(heading, message, icon, time, sound=sound)


def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=0):
    return dialog.yesno(heading, line1, line2, line3, nolabel, int(yeslabel))


def selectDialog(list, heading=addonInfo('name')):
    return dialog.select(heading, list)


def moderator():
    netloc = [urlparse(sys.argv[0]).netloc, '', 'plugin.video.metalliq', 'plugin.video.live.streamspro', 'plugin.video.phstreams', 'plugin.video.cpstreams', 'plugin.video.tinklepad', 'script.tvguide.fullscreen', 'script.tvguide.assassins', 'plugin.program.super.favourites']
    if not infoLabel('Container.PluginName') in netloc:
        sys.exit()


def apiLanguage(ret_name=None):
    langDict = {'Bulgarian': 'bg', 'Chinese': 'zh', 'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 'Finnish': 'fi', 'French': 'fr', 'German': 'de', 'Greek': 'el', 'Hebrew': 'he', 'Hungarian': 'hu', 'Italian': 'it', 'Japanese': 'ja', 'Korean': 'ko', 'Norwegian': 'no', 'Polish': 'pl', 'Portuguese': 'pt', 'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Slovak': 'sk', 'Slovenian': 'sl', 'Spanish': 'es', 'Swedish': 'sv', 'Thai': 'th', 'Turkish': 'tr', 'Ukrainian': 'uk'}
    trakt = ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'th', 'tr', 'uk', 'zh']
    tvdb = ['en', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'fr', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt', 'zh', 'cs', 'sl', 'hr', 'ko']
    youtube = ['gv', 'gu', 'gd', 'ga', 'gn', 'gl', 'ty', 'tw', 'tt', 'tr', 'ts', 'tn', 'to', 'tl', 'tk', 'th', 'ti', 'tg', 'te', 'ta', 'de', 'da', 'dz', 'dv', 'qu', 'zh', 'za', 'zu', 'wa', 'wo', 'jv', 'ja', 'ch', 'co', 'ca', 'ce', 'cy', 'cs', 'cr', 'cv', 'cu', 'ps', 'pt', 'pa', 'pi', 'pl', 'mg', 'ml', 'mn', 'mi', 'mh', 'mk', 'mt', 'ms', 'mr', 'my', 've', 'vi', 'is', 'iu', 'it', 'vo', 'ii', 'ik', 'io', 'ia', 'ie', 'id', 'ig', 'fr', 'fy', 'fa', 'ff', 'fi', 'fj', 'fo', 'ss', 'sr', 'sq', 'sw', 'sv', 'su', 'st', 'sk', 'si', 'so', 'sn', 'sm', 'sl', 'sc', 'sa', 'sg', 'se', 'sd', 'lg', 'lb', 'la', 'ln', 'lo', 'li', 'lv', 'lt', 'lu', 'yi', 'yo', 'el', 'eo', 'en', 'ee', 'eu', 'et', 'es', 'ru', 'rw', 'rm', 'rn', 'ro', 'be', 'bg', 'ba', 'bm', 'bn', 'bo', 'bh', 'bi', 'br', 'bs', 'om', 'oj', 'oc', 'os', 'or', 'xh', 'hz', 'hy', 'hr', 'ht', 'hu', 'hi', 'ho', 'ha', 'he', 'uz', 'ur', 'uk', 'ug', 'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'as', 'ar', 'av', 'ay', 'az', 'nl', 'nn', 'no', 'na', 'nb', 'nd', 'ne', 'ng', 'ny', 'nr', 'nv', 'ka', 'kg', 'kk', 'kj', 'ki', 'ko', 'kn', 'km', 'kl', 'ks', 'kr', 'kw', 'kv', 'ku', 'ky']

    name = None
    name = setting('api.language')
    if not name: name = 'AUTO'

    if name[-1].isupper():
        try:
            name = xbmc.getLanguage(xbmc.ENGLISH_NAME).split(' ')[0]
        except:
            pass
    try:
        name = langDict[name]
    except:
        name = 'de'
    lang = {'trakt': name} if name in trakt else {'trakt': 'en'}
    lang['tvdb'] = name if name in tvdb else 'en'
    lang['youtube'] = name if name in youtube else 'en'

    if ret_name:
        lang['trakt'] = [i[0] for i in langDict.items() if i[1] == lang['trakt']][0]
        lang['tvdb'] = [i[0] for i in langDict.items() if i[1] == lang['tvdb']][0]
        lang['youtube'] = [i[0] for i in langDict.items() if i[1] == lang['youtube']][0]

    return lang


def version():
    num = ''
    try:
        version = addon('xbmc.addon').getAddonInfo('version')
    except:
        version = '999'
    for i in version:
        if i.isdigit():
            num += i
        else:
            break
    return int(num)


def cdnImport(uri, name):
    import imp
    from resources.lib.modules import client
    path = os.path.join(dataPath, 'py' + name)
    if PY2:
        path = path.decode('utf-8')
    deleteDir(os.path.join(path, ''), force=True)
    makeFile(dataPath)
    makeFile(path)
    r = client.request(uri)
    p = os.path.join(path, name + '.py')
    f = openFile(p, 'w')
    f.write(r)
    f.close()
    m = imp.load_source(name, p)
    deleteDir(os.path.join(path, ''), force=True)
    return m


def openSettings():
    try:
        idle()
        id = addonInfo('id')
        execute('Addon.OpenSettings(%s)' % id)
    except:
        return


def getCurrentViewId():
    win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    return str(win.getFocusId())


def refresh():
    return execute('Container.Refresh')


def busy():
    return execute('ActivateWindow(busydialog)')


def idle():
    return execute('Dialog.Close(busydialog)')


def queueItem():
    return execute('Action(Queue)')
