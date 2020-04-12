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
import os
import sqlite3
import xbmc

from resources.lib.modules import client
from resources.lib.modules import source_utils



class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
            

    def movie(self, imdb, title, localtitle, aliases, year):
        try:            
            
            # https://kodi.wiki/view/Special_protocol
            dbPath=xbmc.translatePath('special://home/addons/plugin.video.lastship/resources/movie.db')
            
            
            ## if d doesnt exist automaticall create ##
            # https://stackoverflow.com/questions/11599263/making-it-pythonic-create-a-sqlite3-database-if-it-doesnt-exist
            connection = sqlite3.connect(dbPath)
            connection.execute('CREATE TABLE IF NOT EXISTS stream (imdb TEXT NOT NULL,link TEXT NOT NULL, titel TEXT,season INTEGER,episode INTEGER,quality TEXT DEFAULT "HD")')
            
            ## create cursor ##
            cursor = connection.cursor()                
            sql_query="SELECT link,quality FROM stream WHERE imdb='"+str(imdb)+"'"                
            cursor.execute(sql_query)                
            results =  cursor.fetchall()
            
            url=dict()
            for i in results:                
                link=str(i[0])

                ## Source Utils only accept certain values for quality, so make sure we pass on matching values ##
                if "4" in str(i[1]):
                    quality="4K"
                elif "1080" in str(i[1]):
                    quality="1080p"
                elif "HD" in str(i[1]) or "720" in str(i[1]):
                    quality="HD"
                else:
                    quality="SD"
                
                url[link]=quality
                                
            connection.close()
            print "print feedmed return url",url
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):        
        return imdb

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):

        # https://kodi.wiki/view/Special_protocol
        dbPath=xbmc.translatePath('special://home/addons/plugin.video.lastship/resources/movie.db')
            
        
        ## if d doesnt exist automaticall create ##
        # https://stackoverflow.com/questions/11599263/making-it-pythonic-create-a-sqlite3-database-if-it-doesnt-exist
        connection = sqlite3.connect(dbPath)
        connection.execute('CREATE TABLE IF NOT EXISTS stream (imdb TEXT NOT NULL,link TEXT NOT NULL, titel TEXT,season	INTEGER,episode INTEGER,quality TEXT DEFAULT "HD")')
        ## create cursor ##
        cursor = connection.cursor()        
        sql_query="SELECT link,quality FROM stream WHERE imdb='"+str(imdb)+"'and season="+season+" and episode="+episode+";"        
        cursor.execute(sql_query)                
        results =  cursor.fetchall()        
        url=dict()
                
        for i in results:            
            link=str(i[0])

            ## Source Utils only accept certain values for quality, so make sure we pass on matching values ##
            if "4" in str(i[1]):
                quality="4K"
            elif "1080" in str(i[1]):
                quality="1080p"
            elif "HD" in str(i[1]) or "720" in str(i[1]):
                quality="HD"
            else:
                quality="SD"
                
            url[link]=quality
                                            
        connection.close()
        
        return url

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            for link,quality in url.iteritems():
                                
                if 'google' in link or 'drive' in link:
                    sources.append({'source': 'Google', 'quality': quality , 'language': 'de', 'url':link , 'direct': True, 'debridonly': False})
                    continue
                
                valid, host = source_utils.is_host_valid(link, hostDict)
                if not valid: continue                
                sources.append({'source': host, 'quality': quality, 'language': 'de', 'url':link , 'direct': False, 'debridonly': False,'checkquality':True})
                               
            return sources
        except:
            return sources

    def resolve(self, url):
        try:
            
            if 'google' in url:
                    return self.__google(url)
        
            return url
        except:
            return

    def __search(self, titles, year, content):
        return

    def __google(self, url):
        try:

            if 'view' in url:
                # wenn /view nicht in der URL ist, muss der schritt übersprungen werden
                url = re.sub('[^\/]+$', 'view', url) # fix problem for gvideo urls (/view)        
           

            video_id = re.search('(?<=\/d\/)(.*?)(?=\/)', url).group()
            print "print kinow google videoid",video_id
            
            url = 'https://drive.google.com/uc?id=%s&export=download' % video_id            
            cookie = client.request(url, output='cookie')            
            confirm = '(?<=%s=)(.*?)(?=;)' % video_id
            confirm = re.search(confirm, cookie).group()
            url = 'https://drive.google.com/uc?export=download&confirm=%s&id=%s' % (confirm, video_id)
            url = url + '|Cookie=' + cookie            
            
            return url
        except:
            return url
