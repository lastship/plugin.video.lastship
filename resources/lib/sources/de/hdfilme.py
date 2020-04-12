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

from resources.lib.modules import cleantitle, dom_parser, source_utils, cache
from resources.lib.modules import cfscrape


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['hdfilme.cc']
        self.base_link = 'https://hdfilme.cc'
        self.search_link = '/search?key=%s'
        self.search_api = self.base_link + '/search'
        self.get_link = 'movie/load-stream/%s/%s?'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        titles = source_utils.get_titles_for_search(title, localtitle, aliases)
        url = self.__search(titles, year)
        if url:
            return url
        return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            return {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'localtvshowtitle': localtvshowtitle,
                    'aliases': aliases, 'year': year}
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url: return
            data = url
            titles = source_utils.get_titles_for_search(data['tvshowtitle'], data['localtvshowtitle'], data['aliases'])
            url = self.__search(titles, data['year'], season)
            if not url: return
            urlWithEpisode = url + '/folge-%s' % episode
            return urlparse.urljoin(self.base_link, urlWithEpisode)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url: return sources
            #u'https://hdfilme.cc/the-poison-rose-dunkle-vergangenheit-14882-stream/deutsch'
            query = urlparse.urljoin(self.base_link, url)
            #{'Host': 'hdfilme.cc', 'Upgrade-Insecure-Requests': '1'}
            headers = {'Host': self.domains[0], 'Upgrade-Insecure-Requests': '1'}
            moviecontent = self.scraper.get(query, headers=headers).content
            #'14882'
            movie_id = re.findall(r'data-movie-id="(.+?)"', moviecontent)[0]
            # u'https://hdfilme.cc/the-poison-rose-dunkle-vergangenheit-14882-stream/deutsch.+?id="(.+?)"'
            pattern = '%s.+?id="(.+?)"' % query
            #'130355'
            episode_id = re.findall(pattern, moviecontent)[0]
            #{'referer': u'https://hdfilme.cc/the-poison-rose-dunkle-vergangenheit-14882-stream/deutsch', 'Host': 'hdfilme.cc', 'X-Requested-With': 'XMLHttpRequest'}
            headers = {'Host': self.domains[0], 'X-Requested-With': 'XMLHttpRequest',
                       'referer': urlparse.urljoin(self.base_link, url)}
                       
            #for server in ['', 'server=1']:
            for server in ['']: # nur default Server
                #'movie/load-stream/14882/130355?'
                link = self.get_link % (movie_id,episode_id ) + server
                moviesource = self.scraper.get(urlparse.urljoin(self.base_link, link ), headers=headers)
                if moviesource.status_code != 200: continue

                #'https://load.hdfilme.ws/playlist/203829575d4e8d6602a69a746d7dacf4/203829575d4e8d6602a69a746d7dacf4.m3u8'
                foundsource = re.search('urlVideo.*?\"(.+?)\"', moviesource.content).group(1)
                if foundsource == '': continue
                #'https://load.hdfilme.ws'
                m3u8_base_url =  urlparse.urlparse(foundsource).scheme + '://' + urlparse.urlparse(foundsource).netloc
                #{'origin': 'https://hdfilme.cc', 'referer': u'https://hdfilme.cc/the-poison-rose-dunkle-vergangenheit-14882-stream/deutsch'}
                header = {'origin': self.base_link,'referer': query}

                streamssources = self.scraper.get(foundsource, headers=header)
                if streamssources.status_code != 200: continue
                streams_all = re.findall('RESOLUTION=\d+x([\d]+)\n(.+?)\n',streamssources.content)

                for quality, url in streams_all:
                    if not 'http' in url: url = urlparse.urljoin(m3u8_base_url, url)
                    if server == '': url = url +'|Origin=' + self.base_link + '&Referer=' + query

                    if "1080" in quality:
                        sources.append({'source': 'HDFILME.CC', 'quality': '1080p', 'language': 'de',
                                        'url': url, 'direct': True, 'debridonly': False})
                    elif "720" in quality:
                        sources.append({'source': 'HDFILME.CC', 'quality': '720p', 'language': 'de',
                                        'url': url, 'direct': True, 'debridonly': False})
                    else:
                        sources.append({'source': 'HDFILME.CC', 'quality': 'SD', 'language': 'de',
                                        'url': url, 'direct': True, 'debridonly': False})

            server = 'server=2'
            link = self.get_link % (movie_id, episode_id) + server
            moviesource = self.scraper.get(urlparse.urljoin(self.base_link, link), headers=headers)
            foundsource = re.search('var sources = (\[.*?\]);', moviesource.content).group(1)

            sourcejson = json.loads(foundsource.replace('\'', '"'))
            for sourcelink in sourcejson:
                try:
                    if 'error' in sourcelink['file']: continue
                    url = sourcelink['file'] + '|verifypeer=false&Referer=' + query
                    quality = 'SD'
                    if sourcelink['label'] == '1080p' or sourcelink['label'] == '720p':
                        quality = sourcelink['label']

                    sources.append({'source': 'CDN', 'quality': quality, 'language': 'de', 'url': str(url),
                                    'direct': True, 'debridonly': False})
                except:
                    pass

            return sources
        except:
            return sources

    def resolve(self, url):
        return url

    def __search(self, titles, year, season='0'):
        t = [cleantitle.get(i) for i in set(titles) if i]
        for title in titles:
            try:
                title = cleantitle.query(title)
                query = self.search_link % (urllib.quote_plus(title))
                query = urlparse.urljoin(self.base_link, query)
                headers = {'Referer': self.base_link + '/', 'Host': self.domains[0], 'Upgrade-Insecure-Requests': '1'}
                if season == "0":
                    content = self.scraper.get(query, headers=headers).content
                    searchResult = dom_parser.parse_dom(content, 'div', attrs={'class': 'body-section'})
                    results = re.findall(r'title-product.*?href=\"(.*?)\" title=\"(.*?)\sstream.*?(\d{4})',
                                         searchResult[0].content, flags=re.DOTALL)
                    for x in range(0, len(results)):
                        if year in results[x][2]:
                            title = cleantitle.get(results[x][1])
                            if any(i in title for i in t):
                                url = (results[x][0]) + '/deutsch'
                                return url
                else:
                    #content = self.scraper.get(query, headers=headers).content
                    content = cache.get(self.scraper.get, 48, query, headers=headers).content
                    searchResult = dom_parser.parse_dom(content, 'div', attrs={'class': 'body-section'})
                    results = re.findall(r'title-product.*?href=\"(.*?)\" title=\"(.*?)\"\>.*?(\d{4})',
                                         searchResult[0].content, flags=re.DOTALL)

                    for x in range(0, len(results)):
                        if not year == results[x][2]: continue
                        title = cleantitle.get(results[x][1])
                        if any(i in title for i in t):
                            if "staffel0" + str(season) in title or "staffel" + str(season) in title:
                                if not 'special' in title and not 'special' in i and year == results[x][2]:
                                    return (results[x][0])

                    for x in range(0, len(results)): # ohne 'year'
                        title = cleantitle.get(results[x][1])
                        if any(i in title for i in t):
                            if "staffel0" + str(season) in title or "staffel" + str(season) in title:
                                if not 'special' in title and not 'special' in i:
                                    return (results[x][0])

            except:
                 return
