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

from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib import logger
from string import maketrans
import sys, urllib, urllib2


class cPyLoadHandler:
    def __init__(self):
        self.config = cConfig()

    def sendToPyLoad(self, sPackage, sUrl):
        logger.info('PyLoad package: '+str(sPackage)+', '+str(sUrl))
        if(self.__sendLinkToCore(sPackage, sUrl)==True):
            cGui().showInfo('PyLoad', 'Link gesendet', 5)
        else:
            cGui().showInfo('PyLoad', 'Fehler beim Senden des Links!', 5)
            
    def __sendLinkToCore(self, sPackage, sUrl):
        logger.info('Sending link...')
        
        try:
            py_host = self.config.getSetting('pyload_host')
            py_port = self.config.getSetting('pyload_port')
            py_user = self.config.getSetting('pyload_user')
            py_passwd = self.config.getSetting('pyload_passwd')
            mydata = [('username',py_user),('password',py_passwd)]
            mydata = urllib.urlencode(mydata)

            #check if host has a leading http://
            if(py_host.find('http://') != 0):
                py_host = 'http://'+py_host
            logger.info('Attemting to connect to PyLoad at: '+py_host+':'+py_port)
            req = urllib2.Request(py_host+':'+py_port+'/api/login', mydata)
            req.add_header("Content-type", "application/x-www-form-urlencoded")
            page = urllib2.urlopen(req).read()
            page = page[1:]
            session = page[:-1]
            opener = urllib2.build_opener()
            opener.addheaders.append(('Cookie', 'beaker.session.id='+session))
            #pyLoad doesn't like utf-8, so converting Package name to ascii, also stripping any characters that do not belong into a path name (\/:*?"<>|)
            sPackage=str(sPackage).decode("utf-8").encode('ascii','replace').translate(maketrans('\/:*?"<>|', '_________'))
            py_url=py_host+':'+py_port+'/api/addPackage?name="' + urllib.quote_plus(sPackage) + '"&links=["' + urllib.quote_plus(sUrl) + '"]'
            logger.info('PyLoad API call: '+py_url)
            sock = opener.open(py_url)
            logger.info('123')
            content = sock.read()
            sock.close()
            return True
        except urllib2.HTTPError, e:
            logger.info('unable to send link: Error= '+str(sys.exc_info()[0]))
            logger.info(e.code)
            logger.info(e.read())
            try:
                sock.close()
            except:
                logger.info('unable to close socket...')
            return False
