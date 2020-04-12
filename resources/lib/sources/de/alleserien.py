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
import urllib
import time

from resources.lib.modules import cleantitle, dom_parser, source_utils, cache
from resources.lib.modules import client
#from resources.lib.modules import cfscrape

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        #self.scraper = cfscrape.create_scraper()
        self.url_domain = self.url_domain_checker(url='https://www.allestream.com', slash=True, headers={})
        self.base_link = self.url_domain[0]
        self.domains = [self.url_domain[1]]
        #self.search_link = '/search?search=%s'
        self.search_link_query = self.base_link + '/searchPagination'
        self.link_url = '/getpart'
        self.link_url_movie = '/film-getpart'

    def url_domain_checker(self, url, slash, headers):
        geturl = client.request(url, headers=headers, output='geturl')
        if not url == geturl: url = geturl
        domain = urlparse.urlparse(url).netloc
        if slash is False and url.endswith('/'):url = url[:-1]
        elif slash is True and not url.endswith('/'):url = url + '/'
        return (url, domain)

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            titles = source_utils.get_titles_for_search(title, localtitle, aliases)
            url = self.__search(titles, year, False)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            titles = source_utils.get_titles_for_search(tvshowtitle, localtvshowtitle, aliases)
            url = self.__search(titles, year, True)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            url = urlparse.urljoin(self.base_link, url)

            #r = cache.get(self.scraper.get, 8, url).content
            r = client.request(url)
            seasons = dom_parser.parse_dom(r, "div", attrs={"class": "section-watch-season"})
            for i in seasons:
                seasonNumber = re.search('"seasonNumber">(\d+)', str(i), flags=re.DOTALL).group(1)
                if not seasonNumber == season: continue
                episodes = dom_parser.parse_dom(i, "tr")
                episodes = [(dom_parser.parse_dom(i, "th")[0].content, i.attrs["onclick"]) for i in episodes if "onclick" in i.attrs]
                episodes = [re.findall("'(.*?)'", i[1])[0] for i in episodes if i[0] == episode][0]
                return episodes
            return

        except:
            pass

    def sources(self, url, hostDict, hostprDict):
        _delay = 3
        sources = []
        try:
            if not url:
                return sources
            url = urlparse.urljoin(self.base_link, url)
            #content = self.scraper.get(url).content
            content = client.request(url)

            links = dom_parser.parse_dom(content, 'tr', attrs={'class': 'partItem'})
            links = [(i.attrs['data-id'], i.attrs['data-controlid'], re.findall("(.*)\.png", i.content)[0].split("/")[-1]) for i in
                     links if 'data-id' in i[0]]

            temp = [i for i in links if i[2].lower() == 'vip']
            for id, controlId, host in temp:
                link = self.resolve((url, id, controlId, 'film' in url))

                params = {
                    'Referer': url,
                    'Host': 'alleserienplayer.com'
                }

                time.sleep(_delay)
                result = client.request(link, headers=params)
                #result = self.scraper.get(link, headers=params).content

                result = ((re.findall('"(.*?)"', result)[1]).replace('\\x', '').decode("hex")).decode('base64')
                fp = re.findall('FirePlayer_holaplayer."(.*?)"', result)[0]

                posturl = 'https://alleserienplayer.com/fireplayer/video/%s?do=getVideo ' % fp
                data = {'hash': fp, "r": url}
                params = {
                    'Host': 'alleserienplayer.com',
                    'Origin': 'https://alleserienplayer.com',
                    'X-Requested-With': 'XMLHttpRequest'
                }

                result = client.request(posturl, post=data, headers=params)
                result = json.loads(result)
                result = result['videoSources']

                for i in result:
                    quality = '1080p' if '1080' in i['label'] else '720p' if '720' in i['label'] else 'SD'
                    sources.append({'source': 'CDN', 'quality': quality, 'language': 'de', 'url': i['file'], 'direct': True, 'debridonly': False, 'checkquality': False})

            if len(sources) > 0: return sources
            return

        except:
            return sources

    def resolve(self, url):
        try:
            if 'google' in url:
                return url
            url, id, controlId, movieSearch = url

            content = client.request(url)
            token = re.findall("_token':'(.*?)'", content)[0]

            params = {
                '_token': token,
                'PartID': id,
                'ControlID': controlId
            }

            link = urlparse.urljoin(self.base_link, self.link_url_movie if movieSearch else self.link_url)
            result = client.request(link, post=params)
            if 'false' in result:
                return
            else:
                return dom_parser.parse_dom(result, 'iframe')[0].attrs['src']
        except:

            return

    def __search(self, titles, year, isSerieSearch):
        t = [cleantitle.get(i) for i in set(titles) if i]
        if year != 'None':
            fromYear = int(year)-1
            toYear = int(year)+1

        for title in titles:
            try:
                title = str(title).split('\'')[0]
                title = urllib.quote(cleantitle.query(title))
                req = client.request(self.url_domain[0])
                token = re.findall('_token\':\'(.*?)\'', req)[0]
                posturl = '%spsearch' % self.base_link
                data = {'q': title, "_token": token}
                params = {
                    'Origin': self.base_link[:-1],
                    'Referer': self.base_link,
                    'X-Requested-With': 'XMLHttpRequest'
                }
                html = client.request(posturl, post=data, headers=params)
                results = dom_parser.parse_dom(html, 'a')
                for i in results:
                    img = dom_parser.parse_dom(i, 'img')
                    data_txt_title = img[0][0]['data-txt'].split("(")[0]
                    data_txt_year = int(img[0][0]['data-txt'].split("(")[1][:-1])
                    if isSerieSearch:
                        if cleantitle.get(data_txt_title) in t and 'folge' in i[0]['href'].lower():
                            return i[0]['href']
                    else:
                        if cleantitle.get(data_txt_title) in t and fromYear <= data_txt_year <= toYear and 'filme' in i[0]['href'].lower():
                            return i[0]['href']

            except:
                pass
