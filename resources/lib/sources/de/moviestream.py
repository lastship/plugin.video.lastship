# -*- coding: UTF-8 -*-

"""
    Lastship Add-on (C) 2019
    Credits to Lastship, Placenta and Covenant; our thanks go to their creators

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

import base64
import json
import re
import urllib
import urlparse
import requests
from resources.lib.modules import cleantitle
from resources.lib.modules import directstream
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        
        self.priority = 1
        self.language = ['de']
        self.domains = ['movie-stream.eu']
        self.base_link = 'https://movie-stream.eu'
        self.search_link = '/search?q=%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            imdb = re.sub('[^0-9]', '', imdb)
            titles = [localtitle] + source_utils.aliases_to_array(aliases)
            url = self.__search(titles, year)
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases), year)
            return urllib.urlencode({'url': url, 'imdb': imdb}) if url else None
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            imdb = re.sub('[^0-9]', '', imdb)
            url = self.__search([tvshowtitle], year)
            return urllib.urlencode({'url': url, 'imdb': imdb}) if url else None
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            data.update({'season': season, 'episode': episode})
            return urllib.urlencode(data)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        streamlinks = []

        try:
            if not url:
                return sources

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            url = data['url']
            season = data.get('season')
            episode = data.get('episode')
            if season and episode:
                #we want the current link
                oRequest = cRequestHandler(urlparse.urljoin(self.base_link, url))
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                moviecontent = oRequest.request()
                seasons = re.findall(r'">Staffel((?s).*?)<div class="pull-right">', moviecontent)
                streamlinks.append(re.findall(r'<a href="(.*?)" class="btn btn-sm btn-inline btn', seasons[int(season) - 1])[int(episode) - 1])
            else:
                oRequest = cRequestHandler(urlparse.urljoin(self.base_link, url))
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                moviecontent = oRequest.request()
                streamlinks = re.findall(r'<a href="(.*?)" class="btn btn-sm btn-inline btn', moviecontent)


            for x in range(0, len(streamlinks)):
                oRequest = cRequestHandler(streamlinks[x])
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                moviesource = oRequest.request()
                streams = re.findall(r'class="responsive-embed-item" src="(.*?)" frameborder="', moviesource)
                quality = re.findall(r'class="badge badge-secondary"><font size="5px">(.*?)<', moviesource)

                if "HD" in quality[0] or "1080" in quality[0] or "720" in quality[0]:
                    quality[0] = "720p"
                else:
                    quality[0] = "SD"

                valid, host = source_utils.is_host_valid(streams[0], hostDict)
                if not valid: continue
                sources.append({'source': host, 'quality': quality[0], 'language': 'de', 'url': streams[0], 'direct': False, 'debridonly': False})
                
            return sources
            
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape)
            return sources

    def resolve(self, url):
        return url

    def __search(self, titles, year, season='0'):
        try:
            query = self.search_link % (urllib.quote_plus(cleantitle.query(titles[0])))
            query = urlparse.urljoin(self.base_link, query)

            titles = [cleantitle.get(i) for i in set(titles) if i]
            oRequest = cRequestHandler(query)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            searchResult = oRequest.request()
            results = re.findall(r'<div class=\"movie-title\">\n((?s).*?)\"(.*?)\">(.*?)</a>', searchResult)
        
            usedIndex = 0
            #Find result with matching name and season
            for x in range(0, len(results)):
                title = cleantitle.get(results[x][2])

                if any(i in title for i in titles):
                    return source_utils.strip_domain(results[x][1])
                usedIndex += 1

            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
