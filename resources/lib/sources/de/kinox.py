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

import json
import re
import urllib
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['kinox.fun', 'kinox.fyi', 'kinox.wtf', 'kinox.tv', 'kinos.to', 'kinox.ag', 'kinox.to', 'kinox.me', 'kinox.am', 'kinox.nu', 'kinox.pe', 'kinox.sg', 'kinox.nu', 'kinox.si']
        self._base_link = None
        self.search_link = '/Search.html?q=%s'
        self.get_links_epi = '/aGET/MirrorByEpisode/?Addr=%s&SeriesID=%s&Season=%s&Episode=%s'
        self.mirror_link = '/aGET/Mirror/%s&Hoster=%s&Mirror=%s'

    @property
    def base_link(self):
        if not self._base_link:
            self._base_link = cache.get(self.__get_base_url, 120, 'http://%s' % self.domains[0])
        return self._base_link

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search(imdb)
            if url:
                return urllib.urlencode({'url': url})
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search(imdb)
            if url:
                return urllib.urlencode({'url': url})
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None:
                return

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
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
            url = urlparse.urljoin(self.base_link, data.get('url'))
            season = data.get('season')
            episode = data.get('episode')
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            if season and episode:
                r = dom_parser.parse_dom(r, 'select', attrs={'id': 'SeasonSelection'}, req='rel')[0]
                r = client.replaceHTMLCodes(r.attrs['rel'])[1:]
                r = urlparse.parse_qs(r)
                r = dict([(i, r[i][0]) if r[i] else (i, '') for i in r])
                r = urlparse.urljoin(self.base_link, self.get_links_epi % (r['Addr'], r['SeriesID'], season, episode))
                oRequest = cRequestHandler(r)
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                r = oRequest.request()


            r = dom_parser.parse_dom(r, 'ul', attrs={'id': 'HosterList'})[0]
            r = dom_parser.parse_dom(r, 'li', attrs={'id': re.compile('Hoster_\d+')}, req='rel')
            r = [(client.replaceHTMLCodes(i.attrs['rel']), i.content) for i in r if i[0] and i[1]]
            r = [(i[0], re.findall('class="Named"[^>]*>([^<]+).*?(\d+)/(\d+)', i[1])) for i in r]
            r = [(i[0], i[1][0][0].lower().rsplit('.', 1)[0], i[1][0][2]) for i in r if len(i[1]) > 0]

            for link, hoster, mirrors in r:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue
                u = urlparse.parse_qs('&id=%s' % link)
                u = dict([(x, u[x][0]) if u[x] else (x, '') for x in u])
                for x in range(0, int(mirrors)):
                    tempLink = self.mirror_link % (u['id'], u['Hoster'], x + 1)
                    if season and episode: tempLink += "&Season=%s&Episode=%s" % (season, episode)
                    try: sources.append({'source': hoster, 'quality': 'SD', 'language': 'de', 'url': tempLink, 'direct': False, 'debridonly': False})
                    except: pass

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            r = json.loads(r)['Stream']
            r = [(dom_parser.parse_dom(r, 'a', req='href'), dom_parser.parse_dom(r, 'iframe', req='src'))]
            r = [i[0][0].attrs['href'] if i[0] else i[1][0].attrs['src'] for i in r if i[0] or i[1]][0]

            if not r.startswith('http'):
                r = urlparse.urljoin('http:', r)

            return r
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagResolve)
            return

    def __search(self, imdb):
        try:
            oRequest = cRequestHandler(urlparse.urljoin(self.base_link, self.search_link % imdb))
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            r = dom_parser.parse_dom(r, 'table', attrs={'id': 'RsltTableStatic'})
            r = dom_parser.parse_dom(r, 'tr')
            r = [(dom_parser.parse_dom(i, 'a', req='href'), dom_parser.parse_dom(i, 'img', attrs={'alt': 'language'}, req='src')) for i in r]
            r = [(i[0][0].attrs['href'], i[0][0].content, i[1][0].attrs['src']) for i in r if i[0] and i[1]]
            r = [(i[0], i[1], re.findall('.+?(\d+)\.', i[2])) for i in r]
            r = [(i[0], i[1], i[2][0] if len(i[2]) > 0 else '0') for i in r]
            r = sorted(r, key=lambda i: int(i[2]))  # german > german/subbed
            r = [i[0] for i in r if i[2] in ['1', '15']]

            if len(r) > 0:
                return source_utils.strip_domain(r[0])
            return ""
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, imdb)
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
                    r = dom_parser.parse_dom(r, 'meta', attrs={'name': 'keywords'}, req='content')
                    if r and 'kino.to' in r[0].attrs.get('content').lower():
                        return url
                except:
                    pass
        except:
            pass

        return fallback
