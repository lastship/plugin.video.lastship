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
import urllib
import urlparse

from resources.lib.modules import cleantitle
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['iload.to']
        self.base_link = 'http://iload.to'
        self.search_link = '/suche/%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search(imdb, [localtitle] + source_utils.aliases_to_array(aliases))
            if not url and title != localtitle: url = self.__search(imdb, [title] + source_utils.aliases_to_array(aliases))
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search(imdb, [localtvshowtitle] + source_utils.aliases_to_array(aliases))
            if not url and tvshowtitle != localtvshowtitle: url = self.__search(imdb, [tvshowtitle] + source_utils.aliases_to_array(aliases))
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            query = urlparse.urljoin(self.base_link, url)

            oRequest = cRequestHandler(query)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            r = dom_parser.parse_dom(r, 'td', attrs={'data-title-name': re.compile('Season %02d' % int(season))})
            r = dom_parser.parse_dom(r, 'a', req='href')[0].attrs['href']
            oRequest = cRequestHandler(urlparse.urljoin(self.base_link, r))
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            r = dom_parser.parse_dom(r, 'td', attrs={'data-title-name': re.compile('Episode %02d' % int(episode))})
            r = dom_parser.parse_dom(r, 'a', req='href')[0].attrs['href']

            return source_utils.strip_domain(r)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            query = urlparse.urljoin(self.base_link, url)
            oRequest = cRequestHandler(query)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            content = oRequest.request()
            quality = dom_parser.parse_dom(content, 'div', attrs={'class': 'tabformat'})

            for quali in quality:
                if len(quality) > 1:
                    oRequest = cRequestHandler(urlparse.urljoin(self.base_link, dom_parser.parse_dom(quali, 'a')[0].attrs['href']))
                    oRequest.removeBreakLines(False)
                    oRequest.removeNewLines(False)
                    content = oRequest.request()
                self.__getRelease(sources, content, hostDict)

            self.__getRelease(sources, content, hostDict)

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def __getRelease(self, sources, content, hostDict):
        releases = dom_parser.parse_dom(content, 'table', attrs={'class': 'release-list'})
        releases = dom_parser.parse_dom(releases, 'tr')
        releases = [dom_parser.parse_dom(i, 'a')[0].attrs['href'] for i in releases if len(dom_parser.parse_dom(i, 'img', attrs={'class': 'release-type-stream'})) > 0]

        if len(releases) > 0:
            for release in releases:
                oRequest = cRequestHandler(urlparse.urljoin(self.base_link, release))
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                content = oRequest.request()
                self.__getLinks(sources, content, hostDict, release)
        else:
            self.__getLinks(sources, content, hostDict, dom_parser.parse_dom(content, 'h1')[2].content)

    def __getLinks(self, sources, content, hostDict, release):
        quality, info = source_utils.get_release_quality(release)

        links = dom_parser.parse_dom(content, 'div', attrs={'id': 'ModuleReleaseDownloads'})
        links = dom_parser.parse_dom(links, 'a', attrs={'data-tooltip': 'abspielen'})
        links = [(i.attrs['href'], dom_parser.parse_dom(i, 'img')[0].attrs['src']) for i in links]
        links = [(i[0], re.findall('host/(.*)\.jpg', i[1])[0]) for i in links]

        for link, hoster in links:
            valid, hoster = source_utils.is_host_valid(hoster, hostDict)
            if not valid: continue

            sources.append(
                {'source': hoster, 'quality': quality, 'language': 'de', 'url': link, 'info': info, 'direct': False,
                 'debridonly': False, 'checkquality': True})

    def resolve(self, url):
        try:
            link = urlparse.urljoin(self.base_link, url)
            oRequest = cRequestHandler(link, caching=False)
            content = oRequest.request()
            url = oRequest.getRealUrl()
            return url if self.base_link not in url else None
        except:
            return

    def __search(self, imdb, titles):
        try:
            query = self.search_link % (urllib.quote_plus(cleantitle.query(titles[0])))
            query = urlparse.urljoin(self.base_link, query)

            t = [cleantitle.get(i) for i in set(titles) if i]
            oRequest = cRequestHandler(query)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            r = dom_parser.parse_dom(r, 'div', attrs={'class': 'big-list'})
            r = dom_parser.parse_dom(r, 'table', attrs={'class': 'row'})
            r = dom_parser.parse_dom(r, 'td', attrs={'class': 'list-name'})
            r = dom_parser.parse_dom(r, 'a', req='href')
            r = [i.attrs['href']for i in r if i and cleantitle.get(i.content) in t]
            if len(r) == 0:
                return None
            r = r[0]

            url = source_utils.strip_domain(r)

            oRequest = cRequestHandler(urlparse.urljoin(self.base_link, url))
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            r = dom_parser.parse_dom(r, 'a', attrs={'href': re.compile('.*/tt\d+.*')}, req='href')
            r = [re.findall('.+?(tt\d+).*?', i.attrs['href']) for i in r]
            r = [i[0] for i in r if i]

            return url if imdb in r else None
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
