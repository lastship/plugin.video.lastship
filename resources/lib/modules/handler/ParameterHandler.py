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

import urllib
import sys
import urlparse

class ParameterHandler:

    def __init__(self):          
        params = dict()
        if len(sys.argv)>=3 and len(sys.argv[2])>0:
            params = dict(urlparse.parse_qsl(urlparse.urlsplit(sys.argv[2]).query))
        self.__params = params

    def getAllParameters(self):
        '''
        returns all parameters as dictionary
        '''
        return self.__params

    def getValue(self, paramName):
        '''
        returns value of one parameter as string, if parameter does not exists "False" is returned
        '''
        if (self.exist(paramName)):
            return self.__params[paramName]
            #paramValue = self.__params[paramName]                    
            #return urllib.unquote_plus(paramValue)
        return False

    def exist(self, paramName):
        '''
        checks if paramter with the name "paramName" exists
        '''
        return paramName in self.__params
    
    def setParam(self, paramName, paramValue):
        '''
        set the value of the parameter with the name "paramName" to "paramValue"
        if there is no such parameter, the parameter is created
        if no value is given "paramValue" is set "None"
        '''
        paramValue = str(paramValue)
        self.__params.update( {paramName : paramValue} )


    def addParams(self, paramDict):
        '''
        adds a whole dictionary {key1:value1,...,keyN:valueN} of parameters to the ParameterHandler
        existing parameters are updated
        '''
        for key, value in paramDict.items():
            self.__params.update( {key : str(value)} )


    def getParameterAsUri(self):
        outParams = dict()
        #temp solution
        try:
            del self.__params['params']
        except:
            pass
        try:
            del self.__params['function']
        except:
            pass
        try:
            del self.__params['title']
        except:
            pass
        try:
            del self.__params['site']
        except:
            pass
        
        if len(self.__params) > 0:
            for param in self.__params:
                if len(self.__params[param])<1:
                    continue
                outParams[param]=urllib.unquote_plus(self.__params[param])
            return urllib.urlencode(outParams)
        return 'params=0'