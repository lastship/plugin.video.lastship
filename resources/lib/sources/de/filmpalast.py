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

from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog
from resources.lib.modules import hdgo
from resources.lib.modules.handler.requestHandler import cRequestHandler


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['filmpalast.to']
        self.base_link = 'http://filmpalast.to'
        self.search_link = '/search/title/%s'
        self.stream_link = 'stream/%s/1'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search(
                False, [localtitle] + source_utils.aliases_to_array(aliases), False)
            if not url and title != localtitle:
                url = self.__search(False, [title] + source_utils.aliases_to_array(aliases), False)
            if not url:
                url = self.__search(False, [title] + source_utils.aliases_to_array(aliases), True)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search(
                True, [localtvshowtitle] + source_utils.aliases_to_array(aliases), False)
            if not url and tvshowtitle != localtvshowtitle:
                url = self.__search(
                    True, [tvshowtitle] + source_utils.aliases_to_array(aliases), False)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            episode = '0' + episode if int(episode) < 10 else episode
            season = '0' + season if int(season) < 10 else season

            return re.findall('(.*?)s\d', url)[0] + 's%se%s' % (season, episode)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            query = urlparse.urljoin(self.base_link, url)

            oRequest = cRequestHandler(query)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            quality = dom_parser.parse_dom(r, 'span', attrs={'id': 'release_text'})[
                0].content.split('&nbsp;')[0]
            quality, info = source_utils.get_release_quality(quality)

            r = dom_parser.parse_dom(
                r, 'ul', attrs={'class': 'currentStreamLinks'})
            r = [(dom_parser.parse_dom(i, 'p', attrs={'class': 'hostName'}), re.findall(
                r'(http[^"]+)', i.content)) for i in r]
            r = [(re.sub('\shd', '', i[0][0].content.lower()), i[1][0])
                 for i in r if i[0] and i[1]]

            for hoster, id in r:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if valid:
                    sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'info': '',
                                    'url': id, 'direct': False, 'debridonly': False, 'checkstreams': True})
                else:
                    if 'vivo.php' in id:
                        sources = hdgo.getStreams(id, sources, quality)
            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        return str(url)

    def __search(self, isSerieSearch, titles, isTitleClean):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            if isTitleClean:
                t = [cleantitle.get(self.titleclean(i)) for i in set(titles) if i]
            for title in titles:
                if isTitleClean:
                    title = self.titleclean(title)
                query = self.search_link % (urllib.quote_plus(title))
                query = urlparse.urljoin(self.base_link, query)

                oRequest = cRequestHandler(query)
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                r = oRequest.request()
                r = dom_parser.parse_dom(r, 'article')
                r = dom_parser.parse_dom(r, 'a', attrs={'class': 'rb'}, req='href')
                r = [(i.attrs['href'], i.content) for i in r]

                if len(r) > 0:

                    if isSerieSearch:
                        r = [i[0] for i in r if cleantitle.get(i[1]) in t and not isSerieSearch or cleantitle.get(
                            re.findall('(.*?)S\d', i[1])[0]) and isSerieSearch]

                    else:
                        r = [i[0] for i in r if cleantitle.get(
                            i[1]) in t and not isSerieSearch]

                    if len(r) > 0:
                        url = source_utils.strip_domain(r[0])
                        return url

            return
        except:
            try:
                source_faultlog.logFault(
                    __name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return

    def titleclean(self, title):
        if title is None:
            return
        for i in (':', '!', '!', '!'):  # '!' Platzhalter für weiteres
            if i in title:
                title = title.replace(i, '')
                return title
        if 'II' in title:
            title = title.replace('II', '2')
        elif 'III' in title:
            title = title.replace('III', '3')
        elif 'IV' in title:
            title = title.replace('IV', '4')

        return title

