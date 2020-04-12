# -*- coding: UTF-8 -*-

"""
    Lastship Add-on (C) 2019
    Credits to Placenta and Covenant; our thanks go to their creators

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
# Addon Provider: LastShip

import cookielib, hashlib, httplib, os, socket, sys, time, urllib, urllib2, xbmcgui
from resources.lib.modules import log_utils, cookie_helper, common
from resources.lib.modules.cBFScrape import cBFScrape
from resources.lib.modules.cCFScrape import cCFScrape

class cRequestHandler:
    def __init__(self, sUrl, caching=True, ignoreErrors=True, compression=True):
        self.__sUrl = sUrl
        self.__sRealUrl = ''
        self.__cType = 0
        self.__aParameters = {}
        self.__aResponses = {}
        self.__headerEntries = {}
        self.__cachePath = ''
        self._cookiePath = ''
        self.ignoreDiscard(False)
        self.ignoreExpired(False)
        self.caching = caching
        self.ignoreErrors = ignoreErrors
        self.compression = compression
        self.cacheTime = 600
        self.requestTimeout = 60
        self.removeBreakLines(True)
        self.removeNewLines(True)
        self.__setDefaultHeader()
        self.setCachePath()
        self.__setCookiePath()
        self.__sResponseHeader = ''
        if self.requestTimeout >= 60 or self.requestTimeout <= 10:
            self.requestTimeout = 60

    def removeNewLines(self, bRemoveNewLines):
        self.__bRemoveNewLines = bRemoveNewLines

    def removeBreakLines(self, bRemoveBreakLines):
        self.__bRemoveBreakLines = bRemoveBreakLines

    def setRequestType(self, cType):
        self.__cType = cType

    def addHeaderEntry(self, sHeaderKey, sHeaderValue):
        self.__headerEntries[sHeaderKey] = sHeaderValue

    def getHeaderEntry(self, sHeaderKey):
        if sHeaderKey in self.__headerEntries:
            return self.__headerEntries[sHeaderKey]

    def addParameters(self, key, value, quote=False):
        if not quote:
            self.__aParameters[key] = value
        else:
            self.__aParameters[key] = urllib.quote(str(value))

    def addResponse(self, key, value):
        self.__aResponses[key] = value

    def getResponseHeader(self):
        return self.__sResponseHeader

    def getRealUrl(self):
        return self.__sRealUrl

    def request(self):
        self.__sUrl = self.__sUrl.replace(' ', '+')
        return self.__callRequest()

    def getRequestUri(self):
        return self.__sUrl + '?' + urllib.urlencode(self.__aParameters)

    def __setDefaultHeader(self):
        self.addHeaderEntry('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/56.0')
        self.addHeaderEntry('Accept-Language', 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3')
        self.addHeaderEntry('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        if self.compression:
            self.addHeaderEntry('Accept-Encoding', 'gzip')

    def __callRequest(self):
        if self.caching and self.cacheTime > 0:
            sContent = self.readCache(self.getRequestUri())
            if sContent:
                return sContent

        cookieJar = cookielib.LWPCookieJar(filename=self._cookiePath)
        try:
            cookieJar.load(ignore_discard=self.__bIgnoreDiscard, ignore_expires=self.__bIgnoreExpired)
        except Exception as e:
            log_utils.log(e)

        sParameters = urllib.urlencode(self.__aParameters, True)
        handlers = [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookiejar=cookieJar)]

        if (2, 7, 9) <= sys.version_info < (2, 7, 11):
            handlers.append(newHTTPSHandler)
        opener = urllib2.build_opener(*handlers)
        if (len(sParameters) > 0):
            oRequest = urllib2.Request(self.__sUrl, sParameters)
        else:
            oRequest = urllib2.Request(self.__sUrl)

        for key, value in self.__headerEntries.items():
            oRequest.add_header(key, value)
        cookieJar.add_cookie_header(oRequest)
        user_agent = self.__headerEntries.get('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0')

        try:
            oResponse = opener.open(oRequest, timeout=self.requestTimeout)
        except urllib2.HTTPError, e:
            if e.code == 503 and e.headers.get("Server") == 'cloudflare':
                html = e.read()
                oResponse = self.__check_protection(html, user_agent, cookieJar)
                if not oResponse:
                    log_utils.log("Failed to get CF-Cookie for Url: " + self.__sUrl)
                    return ''
            elif not self.ignoreErrors:
                xbmcgui.Dialog().ok('xStream', 'Fehler beim Abrufen der Url:', self.__sUrl, str(e))
                log_utils.log("HTTPError " + str(e) + " Url: " + self.__sUrl)
                return ''
            else:
                oResponse = e
        except urllib2.URLError, e:
            if not self.ignoreErrors:
                if hasattr(e.reason, 'args') and e.reason.args[0] == 1 and sys.version_info < (2, 7, 9):
                    xbmcgui.Dialog().ok('xStream', str(e.reason), '', 'For this request is Python v2.7.9 or higher required.')
                else:
                    xbmcgui.Dialog().ok('xStream', str(e.reason))
            log_utils.log("URLError " + str(e.reason) + " Url: " + self.__sUrl)
            return ''
        except httplib.HTTPException, e:
            if not self.ignoreErrors:
                xbmcgui.Dialog().ok('xStream', str(e))
            log_utils.log("HTTPException " + str(e) + " Url: " + self.__sUrl)
            return ''

        self.__sResponseHeader = oResponse.info()

        if self.__sResponseHeader.get('Content-Encoding') == 'gzip':
            import gzip
            import StringIO
            sContent = gzip.GzipFile(fileobj=StringIO.StringIO(oResponse.read())).read()
        else:
            sContent = oResponse.read()

        checked_response = self.__check_protection(sContent, user_agent, cookieJar)
        if checked_response:
            oResponse = checked_response
            sContent = oResponse.read()
        cookie_helper.check_cookies(cookieJar)
        cookieJar.save(ignore_discard=self.__bIgnoreDiscard, ignore_expires=self.__bIgnoreExpired)

        if (self.__bRemoveNewLines == True):
            sContent = sContent.replace("\n", "")
            sContent = sContent.replace("\r\t", "")

        if (self.__bRemoveBreakLines == True):
            sContent = sContent.replace("&nbsp;", "")
        self.__sRealUrl = oResponse.geturl()

        oResponse.close()
        if self.caching and self.cacheTime > 0:
            self.writeCache(self.getRequestUri(), sContent)
        return sContent

    def __check_protection(self, html, user_agent, cookie_jar):
        oResponse = None
        if 'cf-browser-verification' in html:
            self.__sUrl = self.__sUrl.replace('https', 'http')
            oResponse = cCFScrape().resolve(self.__sUrl, cookie_jar, user_agent)
        elif 'Blazingfast.io' in html or 'xhr.open("GET","' in html:
            oResponse = cBFScrape().resolve(self.__sUrl, cookie_jar, user_agent)
        return oResponse

    def getHeaderLocationUrl(self):
        opened = urllib2.urlopen(self.__sUrl)
        return opened.geturl()

    def __setCookiePath(self):
        profilePath = common.profilePath
        cookieFile = os.path.join(profilePath, 'cookies.txt')
        if not os.path.exists(cookieFile):
            file = open(cookieFile, 'w')
            file.close()
        self._cookiePath = cookieFile

    def getCookie(self, sCookieName, sDomain=''):
        cookieJar = cookielib.LWPCookieJar()
        try:
            cookieJar.load(self._cookiePath, self.__bIgnoreDiscard, self.__bIgnoreExpired)
        except Exception as e:
            log_utils.log(e)

        for entry in cookieJar:
            if entry.name == sCookieName:
                if sDomain == '':
                    return entry
                elif entry.domain == sDomain:
                    return entry
        return False

    def setCookie(self, oCookie):
        cookieJar = cookielib.LWPCookieJar()
        try:
            cookieJar.load(self._cookiePath, self.__bIgnoreDiscard, self.__bIgnoreExpired)
        except Exception as e:
            log_utils.log(e)
        cookieJar.set_cookie(oCookie)
        cookieJar.save(self._cookiePath, self.__bIgnoreDiscard, self.__bIgnoreExpired)

    def ignoreDiscard(self, bIgnoreDiscard):
        self.__bIgnoreDiscard = bIgnoreDiscard

    def ignoreExpired(self, bIgnoreExpired):
        self.__bIgnoreExpired = bIgnoreExpired

    def setCachePath(self, cache=''):
        if not cache:
            profilePath = common.profilePath
            cache = os.path.join(profilePath, 'htmlcache')
        if not os.path.exists(cache):
            os.makedirs(cache)
        self.__cachePath = cache

    def readCache(self, url):
        h = hashlib.md5(url).hexdigest()
        cacheFile = os.path.join(self.__cachePath, h)
        fileAge = self.getFileAge(cacheFile)
        if 0 < fileAge < self.cacheTime:
            try:
                fhdl = file(cacheFile, 'r')
                content = fhdl.read()
            except:
                log_utils.log('Could not read Cache')
            if content:
                log_utils.log('read html for %s from cache' % url)
                return content
        return ''

    def writeCache(self, url, content):
        h = hashlib.md5(url).hexdigest()
        cacheFile = os.path.join(self.__cachePath, h)
        try:
            fhdl = file(cacheFile, 'w')
            fhdl.write(content)
        except:
            log_utils.log('Could not write Cache')

    @staticmethod
    def getFileAge(cacheFile):
        try:
            fileAge = time.time() - os.stat(cacheFile).st_mtime
        except:
            return 0
        return fileAge

    def clearCache(self):
        files = os.listdir(self.__cachePath)
        for file in files:
            cacheFile = os.path.join(self.__cachePath, file)
            os.remove(cacheFile)

    @staticmethod
    def createUrl(Url, oRequest):
        import urlparse
        parsed_url = urlparse.urlparse(Url)
        netloc = parsed_url.netloc[4:] if parsed_url.netloc.startswith('www.') else parsed_url.netloc
        cfId = oRequest.getCookie('__cfduid', '.' + netloc)
        cfClear = oRequest.getCookie('cf_clearance', '.' + netloc)
        sUrl = ''
        if cfId and cfClear and 'Cookie=Cookie:' not in sUrl:
            delimiter = '&' if '|' in sUrl else '|'
            sUrl = delimiter + "Cookie=Cookie: __cfduid=" + cfId.value + "; cf_clearance=" + cfClear.value
        if 'User-Agent=' not in sUrl:
            delimiter = '&' if '|' in sUrl else '|'
            sUrl += delimiter + "User-Agent=" + oRequest.getHeaderEntry('User-Agent')
        return sUrl

# python 2.7.9 and 2.7.10 certificate workaround
class newHTTPSHandler(urllib2.HTTPSHandler):
    def do_open(self, conn_factory, req, **kwargs):
        conn_factory = newHTTPSConnection
        return urllib2.HTTPSHandler.do_open(self, conn_factory, req)


class newHTTPSConnection(httplib.HTTPSConnection):
    def __init__(self, host, port=None, key_file=None, cert_file=None, strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, context=None):
        import ssl
        context = ssl._create_unverified_context()
        httplib.HTTPSConnection.__init__(self, host, port, key_file, cert_file, strict, timeout, source_address, context)
