# -*- coding: utf-8 -*-

import re
import requests
import simplejson

from resources.lib.modules import cache
from resources.lib.modules import justwatch
# from resources.lib.modules import tvmaze
from resources.lib.modules import source_faultlog


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.api = 'https://apis.justwatch.com/content/titles/de_DE/popular'
        self.provider_id = 171

    def movie(self, imdb, title, localtitle, aliases, year):
        try:

            header = justwatch.get_head()
            payload = justwatch.get_payload(localtitle, ["movie"], ["ads","free"], ["wbx"])

            req = requests.post(self.api, headers=header, json=payload)
            data = req.json()

            offer = justwatch.get_offer(data['items'], year, title, localtitle, self.provider_id)

            if offer:
                url = offer[0]['urls']['standard_web']
                return url
        except:
            return

    # def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
    #     try:

    #         header = justwatch.get_head()
    #         payload = justwatch.get_payload(localtvshowtitle, ["show"], ["ads","free"], ["wbx"])

    #         req = requests.post(self.api, headers=header, json=payload)
    #         data = req.json()

    #         offer = justwatch.get_offer(data['items'], year, tvshowtitle, localtvshowtitle, self.provider_id)

    #         if offer:
    #             show_id = offer[1]
    #             ref = offer[2]
    #             return show_id ,ref

    #     except:
    #         return

    # def episode(self, show_id, imdb, tvdb, title, premiered, season, episode_n):
    #     try:
    #         header = justwatch.get_head(show_id[1])

    #         link = ''
    #         e_nr = tvmaze.tvMaze().episodeAbsoluteNumber(tvdb, season, episode_n)

    #         if int(season) == 1:
    #             s_nr = int(season)
    #         if int(season) >= 2:
    #             s_nr = int(season) -1

    #         url = 'https://apis.justwatch.com/content/titles/show/{}/locale/de_DE'.format(show_id[0])
    #         req = cache.get(requests.get, 6, url, headers=header)
    #         data = req.json()

    #         while link == '':
    #             s_id = data['seasons'][s_nr -1]['id']
    #             # 2te anfrage um aus der season id die folge zu bekommen
    #             url = 'https://apis.justwatch.com/content/titles/show_season/{}/locale/de_DE'.format(s_id)
    #             req = cache.get(requests.get, 6, url, headers=header)
    #             soup = req.json()

    #             if soup['max_episode_number'] > int(e_nr):
    #                 for episode in soup['episodes']:
    #                     if episode['episode_number'] == int(e_nr):
    #                         for offer in episode['offers']:
    #                             if offer['provider_id'] == 171:
    #                                 link = offer['urls']['standard_web']
    #                                 return link
    #                                 break

    #             s_nr += 1
    #             if int(season) + 1 == s_nr:
    #                 link = 'no hit'
    #                 break
    #         return
    #     except:
    #         return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            html = cache.get(requests.get, 6, url)
            url_regex = "hls.*?(http.*?m3u8)"
            link = re.findall(url_regex, html.content)
            link=link[0].replace("\\","")
            sources.append({'source': 'CDN', 'quality': 'SD', 'language': 'de', 'url': link, 'direct': True, 'debridonly': False,'info': ''})

            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, link)
            return sources

    def resolve(self, url):
        return url




