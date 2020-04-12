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
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog
from resources.lib.modules.recaptcha import recaptcha_app


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['cine.to']
        self.base_link = 'https://cine.to'
        self.request_link = '/request/links'
        self.out_link = '/out/%s'
        self.recapInfo = ""

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            return imdb
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources
            data = {'ID': re.findall('\d+', url)[0], 'lang': 2}

            data = cache.get(client.request, 4, urlparse.urljoin(self.base_link, self.request_link), post=data, XHR=True)
            data = json.loads(data)

            if data['status']:
                data = [(i, data['links'][i]) for i in data['links'] if 'links' in data]
                data = [(i[0], i[1][0], (i[1][1:])) for i in data]

                for hoster, quali, links in data:
                    valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                    if not valid: continue

                    quali = int(quali)
                    quali = '1080p' if quali > 2 else '720p' if quali > 1 else 'SD'
                    for link in links:
                        try:
                            sources.append({'source': hoster, 'quality': quali, 'language': 'de', 'url': self.out_link % link,
                                 'direct': False, 'debridonly': False, 'captcha': True, 'info': 'Recaptcha'})
                        except:
                            pass

            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape)
            return sources

    def resolve(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            recap = recaptcha_app.recaptchaApp()

            key = recap.getSolutionWithDialog(url, "6LfV-ioUAAAAANOzmBWxMcw0tQQ4Ut6O6uA-Hi0d", self.recapInfo)
            print "Recaptcha2 Key: " + key

            if key != "" and "skipped" not in key.lower():
                link = client.request(url + '?token=%s' % key, output='geturl')
                if link:
                    return link
            return
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return

    def setRecapInfo(self, info):
        self.recapInfo = info
