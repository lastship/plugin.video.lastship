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

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['kino.cx']
        self.base_link = 'https://kino.cx'
        self.search_link = '?s=%s'
        self.get_hoster = 'wp-admin/admin-ajax.php'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            titles = [localtitle] + source_utils.aliases_to_array(aliases)
            url = self.__search(titles, year)
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases), year)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            url = urlparse.urljoin(self.base_link, url)
            result = cache.get(client.request, 4, url)

            links = dom_parser.parse_dom(result, 'div', attrs={'id': 'playeroptions'})
            links = dom_parser.parse_dom(links, 'li')
            links = [(i.attrs['data-post'], i.attrs['data-nume'], i.attrs['data-type'], dom_parser.parse_dom(i, 'span', attrs={'class': 'server'})[0].content) for i in links if 'trailer' not in i.attrs['data-nume']]

            for post, nume, typ, hoster in links:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue

                sources.append({'source': hoster, 'quality': '720p' if 'unlimited' in hoster else 'SD', 'language': 'de', 'url': (post, nume, typ), 'direct': False, 'debridonly': False, 'checkquality': False})


            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape)
            return sources

    def resolve(self, url):
        post, nume, typ = url

        url = urlparse.urljoin(self.base_link, self.get_hoster)

        params ={
            'action': 'doo_player_ajax',
            'post': post,
            'nume': nume,
            'type': typ
        }

        result = cache.get(client.request, 4, url, post=params)
        url = dom_parser.parse_dom(result, 'iframe')[0].attrs['src']

        return url

    def __search(self, titles, year, season='0'):
        try:
            query = self.search_link % (urllib.quote_plus(cleantitle.query(titles[0])))
            query = urlparse.urljoin(self.base_link, query)

            t = [cleantitle.get(i) for i in set(titles) if i]

            result = cache.get(client.request, 4, query)

            entry = dom_parser.parse_dom(result, 'div', attrs={'class': 'result-item'})
            entry = [(dom_parser.parse_dom(i, 'a')[0], dom_parser.parse_dom(i, 'span', attrs={'class': 'year'})[0]) for i in entry]
            entry = [(i[0].attrs['href'], dom_parser.parse_dom(i[0], 'img')[0].attrs['alt'], i[1].content) for i in entry]
            entry = [i[0] for i in entry if cleantitle.get(i[1]) in t and i[2] == year]

            if len(entry) > 0:
                return source_utils.strip_domain(entry[0])
            else:
                return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
