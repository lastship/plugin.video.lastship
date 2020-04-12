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
import requests
import simplejson
import urllib
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import justwatch
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.api = 'https://apis.justwatch.com/content/titles/de_DE/popular'
        self.provider_id = 28
        self.domains = ['netzkino.de']
        self.base_link = 'http://netzkino.de'
        self.conf_link = '/adconf/android-new.php'
        self.search_link = 'http://api.netzkino.de.simplecache.net/capi-2.0a/search?q=%s&d=www&l=de-DE&v=unknown-debugBuild'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            header = justwatch.get_head()
            payload = justwatch.get_payload(localtitle, ["movie"], ["ads","free"], ["ntz"])

            req = requests.post(self.api, headers=header, json=payload)
            data = req.json()

            offer = justwatch.get_offer(data['items'], year, title, localtitle, self.provider_id)

            if offer:
                link = self.__search([localtitle] + source_utils.aliases_to_array(aliases), imdb, year)
                if not link and title != localtitle: link = self.__search([title] + source_utils.aliases_to_array(aliases), imdb, year)

                return link
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            r = cache.get(client.request, 4, urlparse.urljoin(self.base_link, self.conf_link), XHR=True)
            r = json.loads(r).get('streamer')
            r = cache.get(client.request, 4, r + '%s.mp4/master.m3u8' % url, XHR=True)

            r = re.findall('RESOLUTION\s*=\s*\d+x(\d+).*?\n(http.*?)(?:\n|$)', r, re.IGNORECASE)
            r = [(source_utils.label_to_quality(i[0]), i[1]) for i in r]

            for quality, link in r:
                sources.append({'source': 'CDN', 'quality': quality, 'language': 'de', 'url': link, 'direct': True, 'debridonly': False})

            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources


    def resolve(self, url):
        return url

    def __search(self, titles, imdb, year):
        try:
            query = self.search_link % (urllib.quote_plus(cleantitle.query(titles[0])))
            query = urlparse.urljoin(self.base_link, query)

            t = [cleantitle.get(i) for i in set(titles) if i]
            y = ['%s' % str(year), '%s' % str(int(year) + 1), '%s' % str(int(year) - 1), '0']

            r = cache.get(client.request, 4, query, XHR=True)
            r = json.loads(r)

            r = [(i.get('title'), i.get('custom_fields', {})) for i in r.get('posts', [])]
            r = [(i[0], i[1]) for i in r if i[0] and i[1]]
            r = [(i[0], i[1].get('Streaming', ['']), i[1].get('Jahr', ['0']), i[1].get('IMDb-Link', [''])) for i in r if i]
            r = [(i[0], i[1][0], i[2][0], re.findall('.+?(tt\d+).*?', i[3][0])) for i in r if i[0] and i[1] and i[2] and i[3]]
            r = [i[1] for i in r if imdb in i[3] or (cleantitle.get(i[0]) in t and i[2] in y)]
            if len(r) > 0 :
                return source_utils.strip_domain(r[0])
            return ""


        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch)
            except:
                return
