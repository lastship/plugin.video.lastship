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

import json
import os

from resources.lib import common, logger
from resources.lib.config import cConfig


class cPluginHandler:

    def __init__(self):
        self.addon = common.addon
        self.rootFolder = common.addonPath
        self.settingsFile = os.path.join(self.rootFolder, 'resources', 'settings.xml')
        self.profilePath = common.profilePath
        self.pluginDBFile = os.path.join(self.profilePath,'pluginDB')
        logger.info('profile folder: %s' % self.profilePath)
        logger.info('root folder: %s' % self.rootFolder)
        self.defaultFolder =  os.path.join(self.rootFolder, 'sites')
        logger.info('default sites folder: %s' % self.defaultFolder)

    def getAvailablePlugins(self):
        pluginDB = self.__getPluginDB()
        # default plugins
        update = False
        fileNames = self.__getFileNamesFromFolder(self.defaultFolder)
        for fileName in fileNames:
            plugin = {'name':'', 'icon':'', 'settings':'', 'modified':0}
            if fileName in pluginDB:
                plugin.update(pluginDB[fileName])
            try:
                modTime = os.path.getmtime(os.path.join(self.defaultFolder,fileName+'.py'))
            except OSError:
                modTime = 0
            if fileName not in pluginDB or modTime > plugin['modified']:
                logger.info('load plugin: ' + str(fileName))
                # try to import plugin
                pluginData = self.__getPluginData(fileName)
                if pluginData:
                    pluginData['modified'] = modTime
                    pluginDB[fileName] = pluginData
                    update = True
        # check pluginDB for obsolete entries
        deletions = []
        for pluginID in pluginDB:
            if pluginID not in fileNames:
                deletions.append(pluginID)
        for id in deletions:
            del pluginDB[id]
        if update or deletions:
            self.__updateSettings(pluginDB)
            self.__updatePluginDB(pluginDB)
        return self.getAvailablePluginsFromDB()

    def getAvailablePluginsFromDB(self):
        plugins = []
        oConfig = cConfig()
        iconFolder = os.path.join(self.rootFolder, 'resources','art','sites')
        pluginDB = self.__getPluginDB()
        for pluginID in pluginDB:
            plugin = pluginDB[pluginID]
            pluginSettingsName = 'plugin_%s' % pluginID
            plugin['id'] = pluginID
            if 'icon' in plugin:
                plugin['icon'] = os.path.join(iconFolder, plugin['icon'])
            else:
                plugin['icon'] = ''
            # existieren zu diesem plugin die an/aus settings
            if oConfig.getSetting(pluginSettingsName) == 'true':
                    plugins.append(plugin)
        return plugins

    def __updatePluginDB(self, data):
        if not os.path.exists(self.profilePath):
            os.makedirs(self.profilePath)
        file = open(self.pluginDBFile, 'w')
        json.dump(data,file)
        file.close()

    def __getPluginDB(self):
        if not os.path.exists(self.pluginDBFile):
            return dict()
        file = open(self.pluginDBFile, 'r')
        try:
            data = json.load(file)
        except ValueError:
            logger.error("pluginDB seems corrupt, creating new one")
            data = dict()
        file.close()
        return data

    def __updateSettings(self, pluginData):
        '''
        data (dict): containing plugininformations
        '''
        xmlString = '<plugin_settings>%s</plugin_settings>'
        import xml.etree.ElementTree as ET
        tree = ET.parse(self.settingsFile)
        #find Element for plugin Settings
        pluginElem = False
        for elem in tree.findall('category'):
            if elem.attrib['label']=='30021':
                pluginElem = elem
                break
        if pluginElem is None:
            logger.info('could not update settings, pluginElement not found')
            return False
        pluginElements = pluginElem.findall('setting')
        for elem in pluginElements:
            pluginElem.remove(elem)
        # add plugins to settings
        for pluginID in sorted(pluginData):
            plugin = pluginData[pluginID]
            subEl = ET.SubElement(pluginElem,'setting', {'type': 'lsep', 'label':plugin['name']})
            subEl.tail = '\n    '
            attrib = {'default': 'true', 'type': 'bool'}
            attrib['id'] = 'plugin_%s' % pluginID
            attrib['label'] = '30050'
            subEl = ET.SubElement(pluginElem, 'setting', attrib)
            subEl.tail = '\n    '

            attrib = {'default': str(plugin['globalsearch']).lower(), 'type': 'bool'}
            attrib['id'] = 'global_search_%s' % pluginID
            attrib['label'] = '30052'
            attrib['enable'] = "!eq(-1,false)"
            subEl = ET.SubElement(pluginElem, 'setting', attrib)
            subEl.tail = '\n    '

            if 'settings' in plugin:
                customSettings = []
                try:
                    customSettings = ET.XML(xmlString % plugin['settings']).findall('setting')
                except:
                    logger.info('Parsing of custom settings for % failed.' % plugin['name'])
                for setting in customSettings:
                    setting.tail = '\n    '
                    pluginElem.append(setting)
            subEl = ET.SubElement(pluginElem, 'setting', {'type': 'sep'})
            subEl.tail = '\n    '
        pluginElements = pluginElem.findall('setting')[-1].tail = '\n'
        try:
            ET.dump(pluginElem)
        except:
            logger.info('Settings update failed')
            return
        tree.write(self.settingsFile)

    def __getFileNamesFromFolder(self, sFolder):
        aNameList = []
        items = os.listdir(sFolder)
        for sItemName in items:
            if sItemName.endswith('.py'):
                sItemName = os.path.basename(sItemName[:-3])
                aNameList.append(sItemName)
        return aNameList

    def __getPluginData(self, fileName):
        pluginData = {}
        try:
            plugin = __import__(fileName, globals(), locals())
            pluginData['name'] = plugin.SITE_NAME
        except Exception, e:
            logger.error("Can't import plugin: %s :%s" % (fileName, e))
            return False
        try:
            pluginData['icon'] = plugin.SITE_ICON
        except:
            pass
        try:
            pluginData['settings'] = plugin.SITE_SETTINGS
        except:
            pass
        try:
            pluginData['globalsearch'] = plugin.SITE_GLOBAL_SEARCH
        except:
            pluginData['globalsearch'] = True
            pass
        return pluginData
