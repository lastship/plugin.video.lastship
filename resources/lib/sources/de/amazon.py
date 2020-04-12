# -*- coding: UTF-8 -*-

"""
    Lastship Add-on (C) 2019
    Credits to Lastship; our thanks go to their creators

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
# Addon Provider: Lastship

import re
import requests
import difflib
from resources.lib.modules import cleantitle
from resources.lib.modules import control

BaseUrl = 'https://www.amazon.de'
ATVUrl = 'https://atv-ps-eu.amazon.de'
MarketID = 'A1PA6795UKMFR9'
pkg = 'com.fivecent.amazonvideowrapper'
act = ''

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search(localtitle,year)           
            return url
        except:
            return url

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        url=cleantitle.getsearch(localtvshowtitle)                
        return url

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):        
        localtitle=url        
            
        ### Query Serie
        url="https://atv-ps-eu.amazon.de/cdp/catalog/Search?firmware=fmw:17-app:2.0.45.1210&deviceTypeID=A2M4YX06LWP8WI&deviceID=1&format=json&version=2&formatVersion=3&marketplaceId=A1PA6795UKMFR9&IncludeAll=T&AID=1&searchString="+localtitle+"&OfferGroups=B0043YVHMY&SuppressBlackedoutEST=T&NumberOfResults=40&StartIndex=0"

        data = requests.get(url).json()
       
        for i in data['message']['body']['titles']:
            
            ## Titel abgleich ##
            try:
                #print "print AP episode local title VS. amazon clena title", localtitle,cleantitle.getsearch(str(i['ancestorTitles'][0]['title']))
                #amazontitle =re.sub("\[dt.\/OV\]","",str(i['title']))
                ## try-block weil ChildTitles manchmal leeres ergebnis liefern
                if localtitle in cleantitle.getsearch(str(i['ancestorTitles'][0]['title'])) and not "[ov]" in cleantitle.getsearch(str(i['ancestorTitles'][0]['title'])):
                    #print "print AP TvSow Title found!"
                    ## Season abgleich ##
                    #print "print AP str(season) == str(i['number']", str(season), str(i['number'])
                    try:
                        if str(season) == str(i['number']):
                            #print "print AP TRY S VS S"
                            easin=str(i['childTitles'][0]['feedUrl'])
                            break;
                    except:
                            easin="ERROR"                    
            except:
                continue
        
        ## if notempty ##
        if easin:            
            url="https://atv-ps-eu.amazon.de/cdp/catalog/Browse?firmware=fmw:17-app:2.0.45.1210&deviceTypeID=A2M4YX06LWP8WI&deviceID=d24ff55e99d2e8d6353cd941f9f63fbb3d242b92576e09b6b8a90660&format=json&version=2&formatVersion=3&marketplaceId=A1PA6795UKMFR9&"+easin
            data = requests.get(url).json()
            
            for i in data['message']['body']['titles']:
            
            ## Titel abgleich ##
                try:
                    ## try-block weil ChildTitles manchmal leeres ergebnis liefern
                    prime=i['formats'][0]['offers'][0]['offerType']
                    
                    if prime == "SUBSCRIPTION":
                        #print "print AP Prime Subrsciption",prime
                        if str(episode)==str(i['number']):
                            #print "print Title/EpisodeMAthc "
                            videoid=i['titleId']
                            break;
                except:
                    continue

            return videoid
        else:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        
        try:
            if not url:
                return sources

            if control.setting('provider.amazonapp') == '0':
                sources.append({'source': 'Prime', 'quality': '1080p', 'language': 'de', 'url':'plugin://plugin.video.amazon-test/?mode=PlayVideo&asin='+url , 'info': '', 'direct': True,'local': True, 'debridonly': False})
            if control.setting('provider.amazonapp') == '1':
                sources.append({'source': 'Prime', 'quality': '1080p', 'language': 'de', 'url':'plugin://plugin.video.amazon/?sitemode=PLAYVIDEO&mode=play&asin='+url , 'info': '', 'direct': True,'local': True, 'debridonly': False})
            return sources 

        except:
            return sources

    def resolve(self, url):        
        return url

    def __search(self, localtitle,year):        
        localtitle=cleantitle.getsearch(localtitle)
        
        query="https://atv-ps-eu.amazon.de/cdp/catalog/Search?firmware=fmw:17-app:2.0.45.1210&deviceTypeID=A2M4YX06LWP8WI&deviceID=1&format=json&version=2&formatVersion=3&marketplaceId=A1PA6795UKMFR9&IncludeAll=T&AID=1&searchString="+str(localtitle)+"&NumberOfResults=10&StartIndex=0&Detailed=T"
      
        data = requests.get(query).json()

        streams = []
        for i in data['message']['body']['titles']:            
            stream = {'amazontitle' : '', 'ratio' : '', 'asin' : ''}
            try:
                amazontitle =re.sub("\[dt.\/OV\]","",str(i['title']))                
                amazontitle = unicode(cleantitle.getsearch(amazontitle))                
                ratio=difflib.SequenceMatcher(None, localtitle, amazontitle).ratio()                
                amazonyear = int(str(i['releaseOrFirstAiringDate']['valueFormatted'])[0:4])
                year = int(year)                
                year_ok = False
                for x in range(year-1, year+2):
                    if amazonyear == x:
                        year_ok = True
                stream['amazontitle'] = amazontitle
                stream['ratio'] = ratio
            except:
                continue

            # Der Ratio benötigt ein minimal Wert,da ansosnten ein xbeliebiger ander match genommen wird
            if float(stream['ratio']) > float(0.5):
                
                prime=i['formats'][0]['offers'][0]['offerType']
                                
                if prime == "SUBSCRIPTION":                    
                    asin = i['titleId']
                    stream['asin'] = asin
                else:
                    continue;
                
                if year_ok == True:                    
                    streams.append(stream)
            else:
                continue                
        
        streams = sorted(streams, key = lambda i: i['ratio'])        
        best_asin = streams[len(streams)-1]['asin']        
        return best_asin
