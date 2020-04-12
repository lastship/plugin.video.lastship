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

import re
import json
import httplib
import urllib
import urllib3
from resources.lib.modules import control
try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database


'''
- itemid_liste is returned as list due to different item-ids for 1080p and 4K in movies
- urllib only used for "urllib.quote(title)", whats the urllib3 equivalent?
- emby item query, limit fields? not sure if performance gain but better readability
- embeysearch hints, either pull all items at once or as for now, pull 1 item in each iteration

EMBY FAQ
https://github.com/MediaBrowser/Emby/wiki/Item-Information
swagger.emby.media/?staticview=true#/


'''


class source:
    def __init__(self):
        ## Required Init ##
        self.priority = 1
        self.language = ['de']
        
        ## User Specific ##
        self.name=control.setting('emby.name')
        self.user=control.setting('emby.user')
        self.password=control.setting('emby.pass')
        self.serverip=control.setting('emby.serverip')
        self.server_port=control.setting('emby.port')
        
        self.server="http://"+self.serverip+":"+self.server_port
        self.userid=''
        self.token=''
        self.serverid=''

        # 2 static heads, 1 pre-auth, 1 post-auth being set in def __self.auth..
        self.header_preauth={'Content-Type': 'application/json','Accept-Charset': 'UTF-8,*', 'X-Emby-Authorization': 'MediaBrowser Client="Kodi Lastship",Device="LAssthi",DeviceId="xxx",Version="1.0"', 'Accept-encoding': 'gzip', 'Authorization': 'MediaBrowser Client="Kodi Lasthip",Device="Lastship",DeviceId="xxx",Version="1.0.0"'}
        self.header_postauth={}

        # disable caching: dirty method
        self.sourceFile = control.providercacheFile
        dbcon = database.connect(self.sourceFile)
        dbcur = dbcon.cursor()
        dbcur.execute("DELETE FROM rel_src WHERE source = 'emby'")
        dbcur.execute("DELETE FROM rel_url WHERE source = 'emby'")
        dbcon.commit()
        dbcon.close()

        

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            resp=self.__search(localtitle,"movie")

            if not resp:
                resp=self.__search(title,"movie")
                
            itemid=[]
            
            for i in resp['SearchHints']:
                #print "print emby seatch hints ItemId's",i['ItemId']
                
                ## https://github.com/MediaBrowser/Emby/wiki/Item-Information ##
                #  When retrieving a single item, the entire object is returned. When querying for items, the return data will be stripped to include only a minimal amount of information.
                #  When querying, you can configure the fields that are returned in the output.
                ## End ##
                            
                url = self.server+"/emby/Users/"+self.userid+"/items?Ids="+str(i['ItemId'])+"&Fields=EpisodeCount,SeasonCount,MediaStreams,MediaSources,Overview,ProviderIds&format=json"
                
                http = urllib3.PoolManager()
                r = http.request(
                'GET',
                url,                
                headers=self.header_postauth)
                
                r.release_conn()
                
                resp = json.loads(r.data)

                ## static Items field [0] as we only pull 1 item. Alternatively we could pull all items from /Search/Hints but no advantage seen ##
                
               
                ## compare each item vs. imdb, multiple recors possible due to 1080p and 4K ##                
                
                if str(resp['Items'][0]['ProviderIds']['Imdb'])== imdb:
                        #print "print Emby WE HAVE A MOVIE MATCH"
                        itemid.append(str(i['ItemId']))

                ## return itemid as a list of emby items ##      
                        
            
            return itemid
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            resp=self.__search(localtvshowtitle,"series")
            
           
            for i in resp['SearchHints']:
                #print "print emby seatch hints ItemId's",i['ItemId']
                
                ## https://github.com/MediaBrowser/Emby/wiki/Item-Information ##
                #  When retrieving a single item, the entire object is returned. When querying for items, the return data will be stripped to include only a minimal amount of information.
                #  When querying, you can configure the fields that are returned in the output.
                ## End ##
                
                url = self.server+"/emby/Users/"+self.userid+"/items?Ids="+str(i['ItemId'])+"&Fields=EpisodeCount,SeasonCount,MediaStreams,MediaSources,Overview,ProviderIds&format=json"
                
                http = urllib3.PoolManager()
                r = http.request(
                'GET',
                url,                
                headers=self.header_postauth)
                r.release_conn()
                
                resp_imdb = json.loads(r.data)

                

                if resp_imdb['Items'][0]['ProviderIds']['Imdb'] == imdb:
                    #print "print emby, we have a TVSHOW MATCH!"
                    season_itemid=str(i['ItemId'])
                    break

            ## return season_itemid which is put into the Database and passed to def episode() an never queried again by the scraper for this Series! ##
            
            return season_itemid
        except:
            return
        
    def episode(self, season_itemid, imdb, tvdb, title, premiered, season, episode):
        try:
            if not self.token:
                self.__authenticate()

            itemid_liste=[]
            
            url=self.server+"/emby/Shows/"+season_itemid+"/Episodes?userId="+self.userid+"&Fields=EpisodeCount,SeasonCount,ProviderIds,Overview&format=json"

            http = urllib3.PoolManager()
            r = http.request(
                'GET',
                url,                
                headers=self.header_postauth)

            r.release_conn()
            
            resp = json.loads(r.data)  

                  
            
            for i in resp['Items']:
                #print "print emby search episode ItemId's",i['ParentIndexNumber'],i['IndexNumber'],i['Id']
                
                if str(i['ParentIndexNumber']) == season and str(i['IndexNumber']) == episode:
                    itemid_liste.append(str(i['Id']))
                    break

          
           
            
            return itemid_liste
        except:
            return
        
    def sources(self, itemid_liste, hostDict, hostprDict):
        sources = []
        
        try:
            if not itemid_liste:
                return sources

            print "print sources url",itemid_liste
            return_url={}
             ## Last Call to get ItemProperties for Playback ##
            for itemid in itemid_liste:
                #print "print emby sources loop itemid",itemid
                url = self.server+"/emby/Users/"+self.userid+"/items?Ids="+itemid+"&Fields=EpisodeCount,SeasonCount,MediaStreams,MediaSources,Overview&format=json"
                    
                http = urllib3.PoolManager()
                r = http.request(
                    'GET',
                    url,                
                    headers=self.header_postauth)
                    
                r.release_conn()
                    
                resp = json.loads(r.data)

             
                 ## Extended Info on Emby Streams, Experimental at this stage ##
                info = ""

                ## Media Stream 1 Video & Audio
                try:
                    c1=resp['Items'][0]['MediaSources'][0]['Container']
                    c2=resp['Items'][0]['MediaSources'][0]['MediaStreams'][0]['Codec']
                    c3=""
                    
                    for index,item in enumerate(resp['Items'][0]['MediaSources'][0]['MediaStreams']):
                        if index == 0:
                            continue                        
                        c3+="| "+item['DisplayTitle']
                        if index == 2:
                            break                                      
                    
                    info = c1+" ("+c2+") | "+c3   
                    info = re.sub('Default','',info)
                    info = re.sub('Ger','',info)
                    info = re.sub('stereo','2.0',info)
                except:
                    print "DEBUG: Error: No Extended Infon Emby Stream"

                ## ADditional MediaStreams: 
                info = info.encode('utf-8')

                ## Extended Info on Emby End

                

                if int(resp['Items'][0]['MediaSources'][0]['MediaStreams'][0]['Width']) > 1920:
                    return_url['4K']=self.server+"/emby/Videos/"+str(resp['Items'][0]['Id'])+"/stream?static=true&PlaySessionId=1LIEC3&MediaSourceId="+str(resp['Items'][0]['MediaSources'][0]['Id'])+"&api_key="+self.token
                elif int(resp['Items'][0]['MediaSources'][0]['MediaStreams'][0]['Width']) > 1280:
                    return_url['1080p']=self.server+"/emby/Videos/"+str(resp['Items'][0]['Id'])+"/stream?static=true&PlaySessionId=1LIEC3&MediaSourceId="+str(resp['Items'][0]['MediaSources'][0]['Id'])+"&api_key="+self.token
                elif int(resp['Items'][0]['MediaSources'][0]['MediaStreams'][0]['Width']) > 950:
                    ## 960 x 720 is HD in 4:3 Aspect Ratio
                    return_url['720p']=self.server+"/emby/Videos/"+str(resp['Items'][0]['Id'])+"/stream?static=true&PlaySessionId=1LIEC3&MediaSourceId="+str(resp['Items'][0]['MediaSources'][0]['Id'])+"&api_key="+self.token
                else:
                    return_url['SD']=self.server+"/emby/Videos/"+str(resp['Items'][0]['Id'])+"/stream?static=true&PlaySessionId=1LIEC3&MediaSourceId="+str(resp['Items'][0]['MediaSources'][0]['Id'])+"&api_key="+self.token


            for quality, stream in return_url.items():            
                sources.append({'source': self.name, 'quality': quality, 'language': 'de', 'url': stream,'info': info, 'local': True, 'direct': True, 'debridonly': False})
                
            return sources
        except:
            return sources

    def resolve(self, url):
        try:

            if url:
                
                return url
        except:
            return

    def __authenticate(self):
        try:

            # Body & Header for authentification call #
            messageData = json.dumps({'username':self.user, 'pw':self.password})            
            url = self.server+'/emby/Users/AuthenticateByName?format=json'
            
            ### urllib3 Authentication request ##            
            http = urllib3.PoolManager()           
            r = http.request(
                'POST',
                url,
                body=messageData,
                headers=self.header_preauth)
            r.release_conn()               
            resp = json.loads(r.data)           
       

            ## Set UserId, AccessToken(Api Key) & ServerID, header_postauth
                        
            self.userid=str(resp['User']['Id'])
            self.token=str(resp['AccessToken'])
            self.serverid=str(resp['User']['ServerId'])
            self.header_postauth={'Content-Type': 'application/x-www-form-urlencoded','Accept-Charset': 'UTF-8,*', 'X-Emby-Authorization': 'MediaBrowser UserId='+self.userid+',Client="Kodi Lastship",Device="Lastship",DeviceId="xxx",Version="1.0"', 'Accept-encoding': 'gzip', 'Authorization': 'MediaBrowser UserId='+self.userid+',Client="Kodi Lastship",Device="Lastship",DeviceId="xxx",Version="1.0"', 'X-MediaBrowser-Token':self.token}
            
            
            return 
        except:
            return

        
    def __search(self,title,searchtype):
        try:

            #print "print emby __search type& titel",self,searchtype,type(title),title
            title=re.sub(r"\([0-9]+\)","",title )
            
            self.__authenticate()
            #print "print emby __search after auth",self.userid,self.token,self.serverid
            
            ## create search url, encode whitespaces ##
            query =urllib.quote(title)
            
            url = self.server+"/emby/Search/Hints?searchTerm="+query+"&UserId="+self.userid+"&Limit=10&IncludeItemTypes="+searchtype+"&ExcludeItemTypes=LiveTvProgram&IncludePeople=false&IncludeMedia=true&IncludeGenres=false&IncludeStudios=false&IncludeArtists=false"
                        
            #print "print emby search url",type(url),url
            
            
            ### urllib3 Search Request ###
            
            http =urllib3.PoolManager()      

            r = http.request('GET',url,headers=self.header_postauth)
                      
            r.release_conn()

            resp = json.loads(r.data)

       

            if int(resp['TotalRecordCount']) == 0:
                return
          
            
            return resp
        except:
            return


