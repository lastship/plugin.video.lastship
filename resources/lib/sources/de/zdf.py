# -*- coding: UTF-8 -*-

import requests
import simplejson

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.header = {'Api-Auth': 'Bearer 5bb200097db507149612d7d983131d06c79706d5'}
        self.playerId = 'ngplayer_2_3'


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            episodes = []
            title = cleantitle.getsearch(tvshowtitle)
            url = 'https://www.zdf.de/suche?q={}&from=&to=&attrs=&sender=&contentTypes=episode&sortBy=relevance&synth=true'.format(title)
            req = cache.get(requests.get, 6, url)

            divs = dom_parser.parse_dom(req.text, 'article', attrs={'class': 'b-content-teaser-item'})

            for div in divs:
                date = dom_parser.parse_dom(div, 'time', attrs={'class': 'air-time'})[0].content
                dd, mm, yyyy = date.split('.')
                date = yyyy, mm, dd
                new_day = '-'.join(date)
                link = dom_parser.parse_dom(div, 'a')[0].attrs['href'].split('.')[0]

                episodes.append({'date': new_day,'link': link})

            return episodes

        except:
            source_faultlog.logFault(__name__, source_faultlog.tagSearch)
            return

    def episode(self, episodes, imdb, tvdb, title, premiered, season, episode):
        try:
            if not episodes:
                return
            #print(episodes)
            for vid in episodes:

                if premiered == vid['date']:
                    link = vid['link']
                    break

            if not link:
                return

            url = 'https://api.zdf.de/content/documents/zdf{}.json?profile=player2'.format(link)
            header = self.header
            req = cache.get(requests.get, 6, url, headers=header)

            data = req.json()
            link = data['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd-template']
            return link
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            head = url.split('{')
            tail = head[1].split('}')
            link = head[0] + self.playerId + tail[1]

            url = 'https://api.zdf.de' + link
            header = self.header
            req = cache.get(requests.get, 6, url, headers=header)

            data = req.json()
            link = data['priorityList'][0]['formitaeten'][0]['qualities'][0]['audio']['tracks'][0]['uri']

            sources.append({'source': 'CDN',
                            'quality': '720p',
                            'language': 'de',
                            'url': link,
                            'info': '',
                            'direct': True,
                            'debridonly': False})
            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, link)
            return sources

    def resolve(self, url):
        return url