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
import cfscrape

from resources.lib.modules import cache
from resources.lib.modules import cfscrape
from resources.lib.modules import directstream
from resources.lib.modules.recaptcha import recaptcha_app
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['streamworld.cc']
        self.base_link = 'http://streamworld.cc'
        self.search_link = '/suche.html'

        self.year_link = '/jahr/%d.html'
        self.type_link = '/%s.html'
        self.scraper = cfscrape.create_scraper()

        self.recapInfo = ""

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search([localtitle] + source_utils.aliases_to_array(aliases), year, 'filme')
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases), year, 'filme')
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search([localtvshowtitle] + source_utils.aliases_to_array(aliases), year, 'serien')
            if not url and tvshowtitle != localtvshowtitle: url = self.__search([tvshowtitle] + source_utils.aliases_to_array(aliases), year, 'serien')
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            def __get_correct_link(_url, content, checkval):
                try:
                    if not _url:
                        return

                    _url = urlparse.urljoin(self.base_link, _url)
                    r = cache.get(self.scraper.get, 4, _url).content

                    r = re.findall('<h4>%s[^>]*</h4>(.*?)<div' % content, r, re.DOTALL | re.IGNORECASE)[0]
                    r = re.compile('(<a.+?/a>)', re.DOTALL).findall(''.join(r))
                    r = [(dom_parser.parse_dom(i, 'a', req='href'), dom_parser.parse_dom(i, 'span')) for i in r]
                    r = [(i[0][0].attrs['href'], i[1][0].content) for i in r if i[0] and i[1]]
                    r = [(i[0], i[1] if i[1] else '0') for i in r]
                    r = [i[0] for i in r if int(i[1]) == int(checkval)][0]
                    r = re.sub('/(1080p|720p|x264|3d)', '', r, flags=re.I)

                    return source_utils.strip_domain(r)
                except:
                    return

            url = __get_correct_link(url, 'Staffel', season)
            url = __get_correct_link(url, 'Folge', episode)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            r = cache.get(self.scraper.get, 4, urlparse.urljoin(self.base_link, url)).content

            if 'serie' not in url:
                links = dom_parser.parse_dom(r, 'table')
                links = [i.content for i in links if dom_parser.parse_dom(i, 'span', attrs={'class': re.compile('linkSearch(-a)?')})]
                links = re.compile('(<a.+?/a>)', re.DOTALL).findall(''.join(links))
                links = [dom_parser.parse_dom(i, 'a', req='href') for i in links if re.findall('(.+?)\s*\(\d+\)\s*<', i)]
                links = [i[0].attrs['href'] for i in links if i]

                url = re.sub('/streams-\d+', '', url)
            else:
                links = [url]

            for link in links:
                if '/englisch/' in link: continue

                if link != url: r = cache.get(self.scraper.get, 4, urlparse.urljoin(self.base_link, link)).content

                detail = dom_parser.parse_dom(r, 'th', attrs={'class': 'thlink'})
                detail = [dom_parser.parse_dom(i, 'a', req='href') for i in detail]
                detail = [(i[0].attrs['href'], i[0].content.replace('&#9654;', '').strip()) for i in detail if i]

                if 'serie' in url:
                    detail.append((url, "x264"))

                for release in detail:
                    quality, info = source_utils.get_release_quality(release[1])
                    r = client.request(urlparse.urljoin(self.base_link, release[0]))

                    r = dom_parser.parse_dom(r, 'table')
                    r = [dom_parser.parse_dom(i, 'a', req=['href', 'title']) for i in r if not dom_parser.parse_dom(i, 'table')]
                    r = [(l.attrs['href'], l.attrs['title']) for i in r for l in i if l.attrs['title']]

                    info = ' | '.join(info)
                    info += " Recaptcha"

                    for stream_link, hoster in r:
                        valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                        if not valid: continue

                        direct = False

                        if hoster.lower() == 'gvideo':
                            direct = True

                        sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': stream_link, 'info': info, 'direct': direct, 'debridonly': False, 'checkquality': True, 'captcha': True})

            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            recap = recaptcha_app.recaptchaApp()

            key = recap.getSolutionWithDialog(url, "6LeERkUUAAAAAJH4Yqk-gQH1N6psg0KCuEq_Lkxf", self.recapInfo)
            print "Recaptcha2 Key: " + key
            response = None
            if key != "" and "skipped" not in key.lower():
                response = self.scraper.post(url, data={'g-recaptcha-response': key}, allow_redirects=True)
            elif not response or "skipped" in key.lower():
                return

            if response is not None:
                url = response.url

            if self.base_link not in url:
                if 'google' in url:
                    return directstream.google(url)[0]['url']
            return url
        except Exception as e:
            source_faultlog.logFault(__name__,source_faultlog.tagResolve)
            return

    def __search(self, titles, year, content):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]

            c = client.request(self.base_link, output='cookie')

            p = urllib.urlencode({'search': cleantitle.query(titles[0])})
            c = client.request(urlparse.urljoin(self.base_link, self.search_link), cookie=c, post=p, output='cookie')
            r = client.request(urlparse.urljoin(self.base_link, self.type_link % content), cookie=c, post=p)

            r = dom_parser.parse_dom(r, 'table')[0].content
            r = dom_parser.parse_dom(r, 'tr')
            r = [(dom_parser.parse_dom(i.content, 'a')) for i in r if 'otherLittles' in i.content]
            r = [(i[0].attrs["href"], i[0].content, i[1].content,) for i in r]

            r = sorted(r, key=lambda i: int(i[2]), reverse=True)  # with year > no year

            links = [i[0] for i in r if ((cleantitle.get(i[1]).partition('<')[0] in t) or ("(" in i[1] and cleantitle.get(re.findall("\((.*?)\)", i[1])[0]) in t)) and i[2] == year]

            if len(links) > 0:
                return source_utils.strip_domain(links[0])
            return ""
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return

    def setRecapInfo(self, info):
        self.recapInfo = info