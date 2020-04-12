# -*- coding: UTF-8 -*-

"""
    UpdateManager (C) 2019
	
    Credits to Lastship

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

import urllib
import os
import json

import xbmc
from xbmc import LOGDEBUG, LOGERROR, LOGFATAL, LOGINFO, LOGNONE, LOGNOTICE, LOGSEVERE, LOGWARNING # not in use
from xbmc import translatePath
from xbmcgui import Dialog
from xbmcaddon import Addon as addon

## Android K18 ZIP Fix.
if xbmc.getCondVisibility('system.platform.android') and int(xbmc.getInfoLabel('System.BuildVersion')[:2]) >= 18:
    import fixetzipfile as zipfile
else:import zipfile

PLUGIN = 'Lastship'

## URLRESOLVER
def urlResolverUpdate(silent=False):
    name = 'script.module.urlresolver'
    REMOTE_URLRESOLVER_COMMITS = "https://api.github.com/repos/lastship/script.module.urlresolver/commits/master?access_token=ed4e15498664258c475b0b7da185792cf15a6044"
    REMOTE_URLRESOLVER_DOWNLOADS = "https://api.github.com/repos/lastship/script.module.urlresolver/commits/master?access_token=ed4e15498664258c475b0b7da185792cf15a6044"
    try:
        Update(name, REMOTE_URLRESOLVER_COMMITS, REMOTE_URLRESOLVER_DOWNLOADS, silent)

    except Exception as e:
        log('Exception Raised: %s' % str(e), LOGERROR)
        Dialog().ok('LightScrapers', 'Fehler beim ' + name+ " - Update.")

## LASTSHIP
def pluginVideoLastship(silent=False):
    name = 'plugin.video.lastship'
    REMOTE_PLUGIN_COMMITS = "https://api.github.com/repos/lastship/plugin.video.lastship/commits/nightly"
    REMOTE_PLUGIN_DOWNLOADS = "https://api.github.com/repos/lastship/plugin.video.lastship/zipball/nightly"
    try:
        Update(name, REMOTE_PLUGIN_COMMITS, REMOTE_PLUGIN_DOWNLOADS, silent)

    except Exception as e:
        log('Exception Raised: %s' % str(e), LOGERROR)
        Dialog().ok('LightScrapers', 'Fehler beim ' + name+ " - Update.")


def Update(name, REMOTE_PLUGIN_COMMITS, REMOTE_PLUGIN_DOWNLOADS, silent):
    log('%s - Search for update ' % name, LOGNOTICE)
    try:
        ADDON_DIR = translatePath(addon(name).getAddonInfo('profile')).decode('utf-8')
        LOCAL_PLUGIN_VERSION = os.path.join(ADDON_DIR, "update_sha")
        LOCAL_FILE_NAME_PLUGIN = os.path.join(ADDON_DIR, 'update-' + name + '.zip')
        if not os.path.exists(ADDON_DIR): os.mkdir(ADDON_DIR)
        path = addon(name).getAddonInfo('Path')
        commitXML = _getXmlString(REMOTE_PLUGIN_COMMITS)
        if commitXML:
            isTrue = commitUpdate(commitXML, LOCAL_PLUGIN_VERSION, REMOTE_PLUGIN_DOWNLOADS, path, name, LOCAL_FILE_NAME_PLUGIN, silent)
            if isTrue == True:
                log('%s - Update successful.' % name, LOGNOTICE)
                if silent == False: Dialog().ok(PLUGIN, name + " - Update erfolgreich.")
                return
            elif isTrue == None:
                log('%s - no new update ' % name, LOGNOTICE)
                if silent == False: Dialog().ok(PLUGIN, name + " - Kein Update verfügbar.")
                return

        log('%s - Update error ' % name, LOGERROR)
        Dialog().ok(PLUGIN, 'Fehler beim ' + name + " - Update.")
        return
    except:
        log('%s - Update error ' % name, LOGERROR)
        Dialog().ok(PLUGIN, 'Fehler beim ' + name + " - Update.")


def commitUpdate(onlineFile, offlineFile, downloadLink, LocalDir, name, localFileName, silent):
    try:
        jsData = json.loads(onlineFile)
        if not os.path.exists(offlineFile) or open(offlineFile).read() != jsData['sha']:
            log('%s - start update ' % name, LOGNOTICE)
            isTrue = doUpdate(LocalDir, downloadLink, name, localFileName)
            open(offlineFile, 'w').write(jsData['sha'])
            return True
        else:
            return None

    except Exception as e:
        os.remove(offlineFile)
        log("RateLimit reached")
        return False

def doUpdate(LocalDir, REMOTE_PATH, Title, localFileName):
    try:
        from urllib2 import urlopen
        f = urlopen(REMOTE_PATH)
        # Open our local file for writing
        with open(localFileName,"wb") as local_file:
            local_file.write(f.read())

        updateFile = zipfile.ZipFile(localFileName)

        removeFilesNotInRepo(updateFile, LocalDir)

        for index, n in enumerate(updateFile.namelist()):
            if n[-1] != "/":
                dest = os.path.join(LocalDir, "/".join(n.split("/")[1:]))
                destdir = os.path.dirname(dest)
                if not os.path.isdir(destdir):
                    os.makedirs(destdir)
                data = updateFile.read(n)
                if os.path.exists(dest):
                    os.remove(dest)
                f = open(dest, 'wb')
                f.write(data)
                f.close()
        updateFile.close()
        os.remove(localFileName)
        xbmc.executebuiltin("XBMC.UpdateLocalAddons()")
        return True
    except:
        log("DevUpdate not possible due download error")
        return False

def removeFilesNotInRepo(updateFile, LocalDir):
    ignored_files = ['settings.xml']
    updateFileNameList = [i.split("/")[-1] for i in updateFile.namelist()]

    for root, dirs, files in os.walk(LocalDir):
        if ".git" in root or "pydev" in root or ".idea" in root:
            continue
        else:
            for file in files:
                if file in ignored_files:
                    continue
                if file not in updateFileNameList:
                    os.remove(os.path.join(root, file))

def _getXmlString(xml_url):
    try:
        xmlString = urllib.urlopen(xml_url).read()
        if "sha" in json.loads(xmlString):
            return xmlString
        else:
            log("Update-URL incorrect")
    except Exception as e:
        log(e)

def log(msg, level=LOGDEBUG):
    DEBUGPREFIX = '[ ' + addon().getAddonInfo('name') +' DEBUG ] : '
    # override message level to force logging when addon logging turned on
    level = LOGNOTICE
    try:
        if isinstance(msg, unicode):
            msg = '%s (ENCODED)' % (msg.encode('utf-8'))
        xbmc.log('%s: %s' % (DEBUGPREFIX, msg), level)
    except Exception as e:
        try:
            xbmc.log('Logging Failure: %s' % (e), level)
        except:
            pass  # just give up

#todo Verzeichnis packen -für zukünftige Erweiterung "Backup"
def zipfolder(foldername, target_dir):
    zipobj = zipfile.ZipFile(foldername + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, dirs, files in os.walk(target_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])
    zipobj.close()

def devUpdates():
    try:
        rs = False
        LS = False

        options = ['Beide', 'URL Resolver', 'Lastship']
        result = Dialog().select('Welches Update ausführen?', options)

        if result == 0:
            rs = True
            LS = True
        elif result == 1:
            rs = True
        elif result == 2:
            LS = True

        if LS == True:
            try:
                pluginVideoLastship(False)
            except: pass
        if rs  == True:
            try:
                urlResolverUpdate(False)
            except: pass
        return
    except Exception as e:
        log(e)
