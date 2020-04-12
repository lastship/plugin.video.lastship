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

import re
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['movie4k.sg', 'movie4k.lol', 'movie4k.pe', 'movie4k.tv', 'movie.to', 'movie4k.me', 'movie4k.org', 'movie2k.cm', 'movie2k.nu', 'movie4k.am', 'movie4k.io']
        self._base_link = None
        self.search_link = '/movies.php?list=search&search=%s'

    @property
    def base_link(self):
        if not self._base_link:
            self._base_link = cache.get(self.__get_base_url, 120, 'http://%s' % self.domains[0])
        return self._base_link

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search(False, [localtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and title != localtitle: url = self.__search(False, [title] + source_utils.aliases_to_array(aliases), year)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search(True, [localtvshowtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and tvshowtitle != localtvshowtitle:
                url = self.__search(True, [tvshowtitle] + source_utils.aliases_to_array(aliases), year)
            if url:
                return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return

            url = urlparse.urljoin(self.base_link, url)
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            seasonMapping = dom_parser.parse_dom(r, 'select', attrs={'name': 'season'})
            seasonMapping = dom_parser.parse_dom(seasonMapping, 'option', req='value')
            seasonIndex = [i.attrs['value'] for i in seasonMapping if season in i.content]
            seasonIndex = int(seasonIndex[0]) - 1

            seasons = dom_parser.parse_dom(r, 'div', attrs={'id': re.compile('episodediv.+?')})
            seasons = seasons[seasonIndex]
            episodes = dom_parser.parse_dom(seasons, 'option', req='value')

            url = [i.attrs['value'] for i in episodes if episode == re.findall('\d+', i.content)[0]]
            if len(url) > 0:
                return url[0]
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            url = urlparse.urljoin(self.base_link, url)
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            r = r.replace('\\"', '"')

            links = dom_parser.parse_dom(r, 'tr', attrs={'id': 'tablemoviesindex2'})

            for i in links:
                try:
                    host = dom_parser.parse_dom(i, 'img', req='alt')[0].attrs['alt']
                    host = host.split()[0].rsplit('.', 1)[0].strip().lower()
                    host = host.encode('utf-8')

                    valid, host = source_utils.is_host_valid(host, hostDict)
                    if not valid: continue

                    link = dom_parser.parse_dom(i, 'a', req='href')[0].attrs['href']
                    link = client.replaceHTMLCodes(link)
                    link = urlparse.urljoin(self.base_link, link)
                    link = link.encode('utf-8')

                    sources.append({'source': host, 'quality': 'SD', 'language': 'de', 'url': link, 'direct': False, 'debridonly': False})
                except:
                    pass

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        try:
            h = urlparse.urlparse(url.strip().lower()).netloc
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            r = r.rsplit('"underplayer"')[0].rsplit("'underplayer'")[0]

            u = re.findall('\'(.+?)\'', r) + re.findall('\"(.+?)\"', r)
            u = [client.replaceHTMLCodes(i) for i in u]
            u = [i for i in u if i.startswith('http') and not h in i]

            url = u[-1].encode('utf-8')
            if 'bit.ly' in url:
                oRequest = cRequestHandler(url)
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                oRequest.request()
                url = oRequest.getHeaderLocationUrl()
            elif 'nullrefer.com' in url:
                url = url.replace('nullrefer.com/?', '')

            return url
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagResolve)
            return

    def __search(self, isSerieSearch, titles, year):
        try:
            q = self.search_link % titles[0]
            q = urlparse.urljoin(self.base_link, q)

            t = [cleantitle.get(i) for i in set(titles) if i]
            oRequest = cRequestHandler(q)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            links = dom_parser.parse_dom(r, 'tr', attrs={'id': re.compile('coverPreview.+?')})
            tds = [dom_parser.parse_dom(i, 'td') for i in links]
            tuples = [(dom_parser.parse_dom(i[0], 'a')[0], re.findall('>(\d{4})', i[1].content)) for i in tds if 'ger' in i[4].content]

            tuplesSortByYear = [(i[0].attrs['href'], i[0].content) for i in tuples if year in i[1]]

            if len(tuplesSortByYear) > 0 and not isSerieSearch:
                tuples = tuplesSortByYear
            elif isSerieSearch:
                tuples = [(i[0].attrs['href'], i[0].content) for i in tuples if "serie" in i[0].content.lower()]
            else:
                tuples = [(i[0].attrs['href'], i[0].content) for i in tuples]

            urls = [i[0] for i in tuples if cleantitle.get(i[1]) in t]

            if len(urls) == 0:
                urls = [i[0] for i in tuples if 'untertitel' not in i[1]]

            if len(urls) > 0:
                return source_utils.strip_domain(urls[0])
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return

    def __get_base_url(self, fallback):
        try:
            for domain in self.domains:
                try:
                    url = 'http://%s' % domain
                    oRequest = cRequestHandler(url)
                    oRequest.removeBreakLines(False)
                    oRequest.removeNewLines(False)
                    r = oRequest.request()
                    r = dom_parser.parse_dom(r, 'meta', attrs={'name': 'author'}, req='content')
                    if r and 'movie4k.io' in r[0].attrs.get('content').lower():
                        return url
                except:
                    pass
        except:
            pass

        return fallback
