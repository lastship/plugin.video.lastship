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
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['streamking.media']
        self.base_link = 'https://streamking.media'
        self.search_link = '/search?q=%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            titles = [localtitle] + source_utils.aliases_to_array(aliases)
            url = self.__search(titles, year)
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases), year)
            if not url:
                from resources.lib.modules import duckduckgo
                url = duckduckgo.search(titles, year, self.domains[0], '(.*?)\sstream')
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'localtvshowtitle': localtvshowtitle, 'aliases': aliases, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources
            oRequest = cRequestHandler(urlparse.urljoin(self.base_link, url))
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            moviecontent = oRequest.request()
            results = re.findall(r'data-video-url=\"(.*?)\"', moviecontent)
            quality = re.findall(r'<span class="label label-primary">(.*?)</span>', moviecontent)

            if "HD" in quality:
                quality = "720p"
            else:
                quality = "SD"

            for link in results:
                valid, hoster = source_utils.is_host_valid(link, hostDict)
                if not valid: continue

                sources.append(
                    {'source': hoster, 'quality': quality, 'language': 'de', 'url': link, 'direct': False,
                    'debridonly': False, 'checkquality': True})
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
            oRequest.addHeaderEntry('Referer', 'https://streamking.eu/')
            oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            searchResult = oRequest.request()

            results = dom_parser.parse_dom(searchResult, 'div', attrs={'id': 'section-opt'})
            results = re.findall(r'<a href=\"(.*?)\">(.*?)</a>', results[0].content)
            usedIndex = 0
            #Find result with matching name and season
            for x in range(0, len(results)):
                title = cleantitle.get(results[x][1])

                if any(i in title for i in titles):
                    if season == "0" or ("staffel" in title and ("0"+str(season) in title or str(season) in title)):
                        #We have the suspected link!
                        return source_utils.strip_domain(results[x][0]).decode('utf-8')
                usedIndex += 1

            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
