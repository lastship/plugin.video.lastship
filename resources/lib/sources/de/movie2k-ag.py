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
import urllib
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import dom_parser
from resources.lib.modules import duckduckgo
from resources.lib.modules import source_faultlog
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['movie2k.ag']
        self.base_link = 'https://www.movie2k.ag'
        self.serie_link = 'http://www.vodlocker.to/embed?t=%s'
        self.get_link = 'http://www.vodlocker.to/embed/movieStreams?lang=2&id=%s&server=alternate&cat=%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = duckduckgo.search([localtitle, title] + source_utils.aliases_to_array(aliases), year, self.domains[0], '(.*?)\(')
            query = urlparse.urljoin(self.base_link, url)
            content = cache.get(client.request, 4, query)
            r = dom_parser.parse_dom(content, 'div', attrs={'id': 'player'})
            r = dom_parser.parse_dom(r, 'iframe', req='src')
            r = cache.get(client.request, 4, r[0].attrs['src'])
            r = dom_parser.parse_dom(r, 'span', attrs={'class': 'server'})
            r = dom_parser.parse_dom(r, 'a')[0].attrs['href']
            return self.get_link % (re.findall('id=(\d+)', r)[0], 'movie')
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            return self.serie_link % urllib.quote_plus(localtvshowtitle)
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return
            url += '&season=%s&episode=%s&server=alternate&type=episode' % (season, episode)
            r = cache.get(client.request, 4, url)
            r = re.findall('check_link\?id=(\d+)', r)[0]
            return self.get_link % (r, 'episode') + '&season=%s&episode=%s' % (season, episode)

        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources
            r = cache.get(client.request, 4, url)
            r = dom_parser.parse_dom(r, 'ul', attrs={'id': 'articleList'})
            r = dom_parser.parse_dom(r, 'a')

            for i in r:
                if 'http' in i[0]['href']:
                    link = i[0]['href']
                elif 'http' in i[0]['onclick']:
                    link = re.search('http(.*?)(?=\")', i[0]['onclick']).group()
                else:
                    raise Exception()

                valid, hoster = source_utils.is_host_valid(link, hostDict)
                if not valid: continue

                sources.append({'source': hoster, 'quality': 'SD', 'language': 'de', 'url': link, 'direct': False, 'debridonly': False})

            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        return url
