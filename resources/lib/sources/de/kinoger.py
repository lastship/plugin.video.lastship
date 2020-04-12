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

import urllib
import urlparse
import re
import urlresolver
from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules import cleantitle
from resources.lib.modules import source_faultlog
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['kinoger.com']
        self.base_link = 'http://kinoger.com/'
        self.search = self.base_link + 'index.php?do=search&subaction=search&search_start=1&full_search=0&result_from=1&titleonly=3&story=%s'
        #http://kinoger.com/index.php?do=search&subaction=search&search_start=1&full_search=0&result_from=1&titleonly=3&story=Captain%20Marvel

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search(False, [localtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and title != localtitle:
                url = self.__search(False, [title] + source_utils.aliases_to_array(aliases), year)
            return urllib.urlencode({'url': url, 'imdb': re.sub('[^0-9]', '', imdb)}) if url else None
            
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search(True, [localtvshowtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and tvshowtitle != localtvshowtitle:
                url = self.__search(True, [tvshowtitle] + source_utils.aliases_to_array(aliases), year)
            return urllib.urlencode({'url': url, 'imdb': re.sub('[^0-9]', '', imdb)}) if url else None
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            if not data["url"]:
                return
            data.update({'season': season, 'episode': episode})
            return urllib.urlencode(data)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            url = urlparse.urljoin(self.base_link, data.get('url', ''))
            season = data.get('season')
            episode = data.get('episode')

            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            sHtmlContent = oRequest.request()

            # do we have multiple hoster?
            # i.e. http://kinoger.com/stream/1911-bloodrayne-2-deliverance-2007.html
            link_containers = dom_parser.parse_dom(sHtmlContent,"section")
            if len(link_containers) == 0: #only one, i.e. http://kinoger.com/stream/890-lucy-2014.html
                #only one
                link_containers = dom_parser.parse_dom(sHtmlContent,"div",attrs={"id":"container-video"})
            for container in link_containers:
                #3 different types found till now: hdgo.show, namba.show and direct (mail.ru etc.)
                # i.e. http://kinoger.com/stream/1911-bloodrayne-2-deliverance-2007.html
                quality = "SD"
                if ".show" in container.content:
                    pattern = ',\[\[(.*?)\]\]'
                    links = re.compile(pattern, re.DOTALL).findall(container.content)
                    if len(links) == 0: continue;
                    #split them up to get season and episode
                    season_array = links[0].split("],[")

                    source_link = None
                    if season and episode:
                        if len(season_array) < int(season):
                            continue
                        episode_array = season_array[int(season)-1].split(",")
                        if len(episode_array) < int(episode):
                            continue
                        source_link = episode_array[int(episode)-1]
                    elif len(season_array) == 1:
                        source_link = season_array[0]

                    if source_link:
                        source_link = source_link.strip("'")

                        valid, host = source_utils.is_host_valid(source_link, hostDict)
                        if valid:
                            resolveurl = urlresolver.resolve(source_link)
                            if "quali" in resolveurl:
                                quality = re.findall('quali.*?=(.*?)\|', resolveurl)[0]
                            sources.append({'source': host, 'quality': quality, 'language': 'de', 'url': source_link, 'direct': False,
                                            'debridonly': False, 'checkstreams': True})

                        elif "namba" in container.content:
                            sources.append({'source': 'kinoger.com', 'quality': quality, 'language': 'de', 'url': "http://v1.kinoger.pw/vod/"+source_link, 'direct': False,
                                    'debridonly': False, 'checkquality': True})

                elif "iframe" in container.content:

                    frame = dom_parser.parse_dom(container.content, "iframe")
                    if len(frame) == 0:
                        continue
                    else:
                        valid, host = source_utils.is_host_valid(frame[0].attrs["src"], hostDict)
                        if not valid: continue
                        resolveurl = urlresolver.resolve(frame[0].attrs["src"])
                        if "quali" in resolveurl:
                            quality = re.findall('quali.*?=(.*?)\|', resolveurl)[0]
                        sources.append({'source': host, 'quality': quality, 'language': 'de', 'url': frame[0].attrs["src"], 'direct': False,
                                        'debridonly': False, 'checkstreams': True})
                else:
                    continue

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources


    def resolve(self, url):
        try:
            if 'kinoger' in url:
                oRequest = cRequestHandler(url)
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                request = oRequest.request()
                pattern = 'src:  "(.*?)"'
                request = re.compile(pattern, re.DOTALL).findall(request)
                return request[0] + '|Referer=' + url
            return url
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return url

    def __search(self, isSerieSearch, titles, year):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            url = self.search % titles[0]
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            sHtmlContent = oRequest.request()
            search_results = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'class': 'title'})
            search_results = dom_parser.parse_dom(search_results, 'a')
            search_results = [(i.attrs['href'], i.content) for i in search_results]
            search_results = [(i[0], re.findall('(.*?)\((\d+)', i[1])[0]) for i in search_results]
            
            if isSerieSearch == True:
                for x in range(0, len(search_results)):
                    title = cleantitle.get(search_results[x][1][0])
                    if 'staffel' in title and any(k in title for k in t):
                        return source_utils.strip_domain(search_results[x][0])
            else:
                for x in range(0, len(search_results)):
                    title = cleantitle.get(search_results[x][1][0])
                    if any(k in title for k in t) and year == search_results[x][1][1]:
                        return source_utils.strip_domain(search_results[x][0])

            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
