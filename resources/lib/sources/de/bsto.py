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

import urlparse
from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser
from resources.lib.modules import client
from resources.lib.modules import source_faultlog
from resources.lib.modules import source_utils
from resources.lib.modules.recaptcha import recaptcha_app
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['bs.to']
        self.base_link = 'https://bs.to/'
        self.search_link = self.base_link + 'andere-serien'
        self.recapInfo = ''

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search([localtvshowtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and tvshowtitle != localtvshowtitle: url = self.__search([tvshowtitle] + source_utils.aliases_to_array(aliases), year)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            oRequest = cRequestHandler( urlparse.urljoin(self.base_link, url) + "/" + season)
            content = oRequest.request()
            link = dom_parser.parse_dom(content, 'table', attrs={'class': 'episodes'})
            link = dom_parser.parse_dom(link, 'a')
            link = [i.attrs['href'] for i in link if i.content == episode]

            return link[0]
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources
            oRequest = cRequestHandler(urlparse.urljoin(self.base_link, url))
            content = oRequest.request()
            links = dom_parser.parse_dom(content, 'a')
            links = [i for i in links if 'href' in i.attrs and url in i.attrs['href']]
            links = [(i.attrs['href'], i.attrs['title'].replace('HD', ''), '720p' if 'HD' in i.attrs['href'] else 'SD') for i in links if 'title' in i.attrs]

            for link, hoster, quality in links:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue
                sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'info': 'Recaptcha', 'url': link, 'direct': False, 'debridonly': False, 'captcha': True})

            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape)
            return sources

    def resolve(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)
            
            oRequest = cRequestHandler(url, caching=False)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            content = oRequest.request()
            content = client.request(url)
            url = dom_parser.parse_dom(content, 'iframe')[0].attrs['src']

            recap = recaptcha_app.recaptchaApp()

            key = recap.getSolutionWithDialog(url, "6LeiZSYUAAAAAI3JZXrRnrsBzAdrZ40PmD57v_fs", self.recapInfo)
            print "Recaptcha2 Key: " + key
            response = None
            if key != "" and "skipped" not in key.lower():
                content = client.request(url)
                s = dom_parser.parse_dom(content, 'input', attrs={'name': 's'})[0].attrs['value']
                link = client.request(url + '?t=%s&s=%s' % (key, s), output='geturl')
                return link
            elif not response or "skipped" in key.lower():
                return
        except Exception as e:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return

    def __search(self, titles, year):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            oRequest = cRequestHandler(self.search_link)
            content = oRequest.request()

            links = dom_parser.parse_dom(content, 'div', attrs={'id': 'seriesContainer'})
            links = dom_parser.parse_dom(links, 'a')
            links = [i.attrs['href'] for i in links if cleantitle.get(i.attrs['title']) in t]

            if len(links) > 0:
                return links[0]
            else:
                return
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagSearch)
            return

    def setRecapInfo(self, info):
        self.recapInfo = info
