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

import base64
import json
import re
from binascii import unhexlify

from resources.lib.modules import cfscrape
from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules import source_utils
from resources.lib.modules import utils
from resources.lib.modules.handler.requestHandler import cRequestHandler
from resources.lib.modules.handler.ParameterHandler import ParameterHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['hd-streams.org']
        self.base_link = 'https://hd-streams.org/'
        self.movie_link = self.base_link + 'movies?perPage=54'
        self.movie_link = self.base_link + 'seasons?perPage=54'
        self.search = self.base_link + 'search?q=%s&movies=true&seasons=true&actors=false&didyoumean=false'
        self.recapInfo = ""

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            objects = self.__search(imdb, True)

            t = [cleantitle.get(i) for i in set(source_utils.aliases_to_array(aliases)) if i]
            t.append(cleantitle.get(title))
            t.append(cleantitle.get(localtitle))

            for i in range(1, len(objects)):
                if cleantitle.get(objects[i]['title']) in t:
                    return objects[i]['url']
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            objects = self.__search(imdb, False)

            t = [cleantitle.get(i) for i in set(source_utils.aliases_to_array(aliases)) if i]
            t.append(cleantitle.get(tvshowtitle))
            t.append(cleantitle.get(localtvshowtitle))

            for i in range(1, len(objects)):
                if cleantitle.get(objects[i]['title']) in t:
                    return objects[i]['seasons']
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            url = [i['url'] for i in url if 'season/' + season in i['url']]

            return url[0], episode
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            if isinstance(url, tuple):
                url, episode = url
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            if "serie" in url:
                links = self._getSeriesLinks(r, episode)
            else:
                links = self._getMovieLinks(r)

            for e, h, sName, quali in links:
                valid, hoster = source_utils.is_host_valid(sName, hostDict)
                if not valid: continue

                isCaptcha = 'grecaptcha' in r
                sources.append({'source': hoster, 'quality': quali, 'language': 'de', 'url': (e, h, url, isCaptcha), 'info': "Recaptcha" if isCaptcha else '', 'direct': False, 'debridonly': False, 'captcha': True})

            return sources
        except Exception:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources

    def __getlinks(self, e, h, url, key):
        try:
            url = url + '/stream'
            params = {'e': e, 'h': h, 'lang': 'de', 'q': '', 'grecaptcha': key}
            oRequest = cRequestHandler(url[:-7])
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            csrf = dom_parser.parse_dom(r, "meta", attrs={"name": "csrf-token"})[0].attrs["content"]
            oRequest = cRequestHandler(url)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            oRequest.addHeaderEntry('X-CSRF-TOKEN', csrf)
            oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
            oRequest.addParameters('e', e)
            oRequest.addParameters('h', h)
            oRequest.addParameters('lang', 'de')
            oRequest.addParameters('q', '')
            oRequest.addParameters('grecaptcha', key)
            oRequest.setRequestType(1)
            sHtmlContent = oRequest.request()
            helper = json.loads(sHtmlContent)

            mainData = utils.byteify(helper)

            tmp = mainData.get('d', '') + mainData.get('c', '') + mainData.get('iv', '') + mainData.get('f','') + mainData.get('h', '') + mainData.get('b', '')

            tmp = utils.byteify(json.loads(base64.b64decode(tmp)))

            salt = unhexlify(tmp['s'])
            ciphertext = base64.b64decode(tmp['ct'][::-1])
            b = base64.b64encode(csrf[::-1])

            tmp = utils.cryptoJS_AES_decrypt(ciphertext, b, salt)

            tmp = utils.byteify(json.loads(base64.b64decode(tmp)))
            ciphertext = base64.b64decode(tmp['ct'][::-1])
            salt = unhexlify(tmp['s'])
            b = ''
            a = csrf
            for idx in range(len(a) - 1, 0, -2):
                b += a[idx]
            if mainData.get('e', None):
                b += '1'
            else:
                b += '0'
            tmp = utils.cryptoJS_AES_decrypt(ciphertext, str(b), salt)

            return utils.byteify(json.loads(tmp))
        except Exception:
            return

    def resolve(self, url):
        try:
            e, h, url, recaptcha = url
            key = ''       
            if recaptcha:
                from resources.lib.modules.recaptcha import recaptcha_app
                recap = recaptcha_app.recaptchaApp()
                key = recap.getSolutionWithDialog(url, "6LdWQEUUAAAAAOLikUMWfs8JIJK2CAShlLzsPE9v", self.recapInfo)
            return self.__getlinks(e, h, url, key)
        except:
            return

    def __search(self, imdb, isMovieSearch):
        try:
            oRequest = cRequestHandler(self.base_link)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            sHtmlContent = oRequest.request()

            pattern = '<meta name="csrf-token" content="([^"]+)">'
            string = str(sHtmlContent)
            token = re.compile(pattern, flags=re.I | re.M).findall(string)

            if len(token) == 0:
                return #No Entry found?
            # first iteration of session object to be parsed for search
            oRequest = cRequestHandler(self.search % imdb)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            oRequest.addHeaderEntry('X-CSRF-TOKEN', token[0])
            oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
            sHtmlContent = oRequest.request()

            content = json.loads(sHtmlContent)
            if isMovieSearch:
                returnObjects = content["movies"]
            else:
                returnObjects = content["series"]

            return returnObjects
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, imdb)
            except:
                return
        return

    def setRecapInfo(self, info):
        self.recapInfo = info

    def _getMovieLinks(self, content):
        links = dom_parser.parse_dom(content, "v-tabs")
        links = [i for i in links if 'alt="de"' in dom_parser.parse_dom(i, "v-tab")[0].content]
        links = dom_parser.parse_dom(links, "v-tab-item")
        links = dom_parser.parse_dom(links, "v-flex")
        links = [dom_parser.parse_dom(i, "v-btn") for i in links]
        links = [[(a.attrs["@click"], re.findall("\n(.*)", a.content)[0].strip(), i[0].content) for a in i if
                  "@click" in a.attrs] for i in links]
        links = [item for sublist in links for item in sublist]
        links = [(re.findall("\d+", i[0]), i[1], i[2]) for i in links]
        return [(i[0][0], i[0][1], i[1], i[2]) for i in links]

    def _getSeriesLinks(self, content, episode):
        links = dom_parser.parse_dom(content, "div", attrs={'class': "episode"})
        links = [(dom_parser.parse_dom(i, "v-list-tile"), dom_parser.parse_dom(i, "p", attrs={'class': "episode-number"})[0]) for i in links]
        links = [i[0] for i in links if episode == re.findall("\d+", i[1].content)[0]][0]
        links = [(a.attrs["@click.native"], dom_parser.parse_dom(a.content, 'v-list-tile-title')[0].content) for a in links]

        links = [(re.findall("'(.*?)'", i[0]), i[1]) for i in links]
        return [(i[0][0], i[0][1], re.findall("(.*?)\d", i[1])[0].strip(), i[0][2]) for i in links]
