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

## MaxDome API Documentation: https://github.com/LizMyers/Maxdome/blob/master/MXDDOC-2.2.1Filteraliases-121017-1521-54.pdf
#


import requests
import simplejson
from resources.lib.modules import cleantitle


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.headers = {'accept':'application/vnd.maxdome.im.v8+json', 'Accept-Encoding':'gzip, deflate, sdch', 'Accept-Language':'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4', 'client':'mxd_package', 'clienttype': 'webportal', 'Connection': 'keep-alive', 'content-type':'application/json','language':'de_DE', 'Maxdome-Origin':'maxdome.de', 'platform':'web'}

    

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            title=cleantitle.getsearch(localtitle)
            url= 'https://heimdall.maxdome.de/api/v1/assets?filter[]=search~' + title + '&filter=hasPackageContent&pageSize=50&pageStart=1'
            r = requests.get(url, headers=self.headers)            
            data = r.json()
            md_film_id=""

            for i in data['assetList']:            
                #print "print titelname & titel",i['title'],title
                if cleantitle.getsearch(i['title']) in title or title in cleantitle.getsearch(i['title']):
                    #print "print MD Titel id match", i['id'],i['title']  
                    md_film_id=str(i['id'])   
                    break 
        
            return md_film_id
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):

        url=cleantitle.getsearch(localtvshowtitle)
                
        return url

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        
        localtitle=url              
        
        url= 'https://heimdall.maxdome.de/api/v1/assets/?filter=search~' + localtitle + '&filter=seasonNumber~' + season + '&filter=episodeNumber~'+ episode + '&filter=hasPackageContent&pageSize=50&pageStart=1'
        r = requests.get(url, headers=self.headers)             
        data = r.json()

        md_film_id=""        
                
        for index,i in enumerate(data['assetList']):            
            if str(i['seasonNumber']) == str(season) and str(episode)== str(i['episodeNumber']):
                md_film_id=str(i['id'])
                break
 
        return md_film_id

    def sources(self, url, hostDict, hostprDict):
        sources = []
        
        try:
            if not url:
                return sources
            
            sources.append({'source': 'Premium', 'quality': '1080p', 'language': 'de', 'url': 'plugin://plugin.video.maxdome/?action=play&id=' + url,'local': True, 'direct': True, 'debridonly': False})
           
            return sources
        except:
            return sources

    def resolve(self, url):        

        return url

   
        
   
