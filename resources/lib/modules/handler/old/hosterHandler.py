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

import urlresolver

from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser


class cHosterHandler:

    def getUrl(self, oHoster):
        sUrl = oHoster.getUrl()
        if (oHoster.checkUrl(sUrl)):
            oRequest = cRequestHandler(sUrl)            
            sContent = oRequest.request()
            pattern = oHoster.getPattern()
            if type(pattern) == type(''):
                aMediaLink = cParser().parse(sContent, oHoster.getPattern())
                if (aMediaLink[0] == True):
                    logger.info('hosterhandler: ' + aMediaLink[1][0])
                    return True, aMediaLink[1][0]
            else:
                for p in pattern:
                    aMediaLink = cParser().parse(sContent, p)
                    if (aMediaLink[0] == True):
                        logger.info('hosterhandler: ' + aMediaLink[1][0])
                        return True, aMediaLink[1][0]
                        
        return False, ''

    def getHoster2(self, sHoster):    
        # if (sHoster.find('.') != -1):
            # Arr = sHoster.split('.')
            # if (Arr[0].startswith('http') or Arr[0].startswith('www')):
                # sHoster = Arr[1]
            # else:
                # sHoster = Arr[0]
        return self.getHoster(sHoster)        
    '''
    checks if there is a resolver for a given hoster or url
    '''    
    def getHoster(self, sHosterFileName):
        if sHosterFileName != '':
            source = [urlresolver.HostedMediaFile(url=sHosterFileName)]
            if (urlresolver.filter_source_list(source)):
                return source[0].get_host()
            # media_id is in this case only a dummy
            source = [urlresolver.HostedMediaFile(host=sHosterFileName, media_id='ABC123XYZ')]            
            if (urlresolver.filter_source_list(source)):
                return source[0].get_host()
        return False   