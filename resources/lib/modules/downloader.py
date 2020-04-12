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

import re
import json
import urllib
import urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcvfs
import os
import inspect


def download(name, image, url):
    if url == None: return

    from resources.lib.modules import control
    from resources.lib.modules import trakt

    try: headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except: headers = dict('')

    url = url.split('|')[0]

    sorter = re.compile('(.+?)\sS(\d*)E\d*$').findall(name)
    
    if control.setting('Download.auf.Deutsch') != 'false': #Option für Benennung auf Deutsch EIN
        if len(sorter) == 0: #Filme
            title = name [:-7]
            transyear = name.replace("(","").replace(")","")
            year = transyear [-4:]
            imdb = trakt.SearchMovie(title, year, full=False)[0]
            imdb = imdb.get('movie', '0')
            imdb = imdb.get('ids', {}).get('imdb', '0')
            imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
            lang = 'de'
            germantitle = trakt.getMovieTranslation(imdb, lang)
            transname = germantitle.translate(None, '\/:*?"<>|').strip('.') + ' ' + '(' + str(year) + ')'
            name = transname
            levels =['../../../..', '../../..', '../..', '..']
            dest = control.setting('movie.download.path')
            dest = control.transPath(dest)
            for level in levels:
                try: control.makeFile(os.path.abspath(os.path.join(dest, level)))
                except: pass
            control.makeFile(dest)
            dest = os.path.join(dest, transname)
            control.makeFile(dest)
            ext = os.path.splitext(urlparse.urlparse(url).path)[1][1:]
            if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']: ext = 'mp4'
            dest = os.path.join(dest, transname + '.' + ext)
        else: #Serien
            title = name [:-7]
            transyear = name.replace("(","").replace(")","")
            year = transyear [-4:] #dirty year.... but working)
            episode = name.rsplit(' ', 1)
            imdb = trakt.SearchTVShow(title, year, full=False)[0]
            imdb = imdb.get('show', '0')
            imdb = imdb.get('ids', {}).get('imdb', '0')
            imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
            lang = 'de'
            germantitle = trakt.getTVShowTranslation(imdb, lang)
            transname = germantitle.translate(None, '\/:*?"<>|').strip('.')
            content = re.compile('(.+?)\sS(\d*)E\d*$').findall(name)
            transtvshowtitle = content[0][0].translate(None, '\/:*?"<>|').strip('.')
            name = transname
            levels =['../../../..', '../../..', '../..', '..']
            dest = control.setting('tv.download.path')
            dest = control.transPath(dest)
            for level in levels:
                try: control.makeFile(os.path.abspath(os.path.join(dest, level)))
                except: pass
            control.makeFile(dest)
            dest = os.path.join(dest, transname)
            control.makeFile(dest)
            ext = os.path.splitext(urlparse.urlparse(url).path)[1][1:]
            if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']: ext = 'mp4'
            DownloadSeasonName = control.setting('Download.Season.Name')
            if DownloadSeasonName == '0':
                dest = os.path.join(dest, 'Season %01d' % int(content[0][1]))
            else:
                pass
            if DownloadSeasonName == '1':
                dest = os.path.join(dest, 'S%01d' % int(content[0][1]))
            else:
                pass
            if DownloadSeasonName == '2':
                dest = os.path.join(dest, 'Staffel %01d' % int(content[0][1]))
            else:
                pass
            control.makeFile(dest)
            dest = os.path.join(dest, transname + ' ' + episode[1] + '.' + ext)
    else: #Option für Benennung auf Deutsch AUS
        if len(sorter) == 0: #Filme
            transname = name.translate(None, '\/:*?"<>|').strip('.')
            levels =['../../../..', '../../..', '../..', '..']
            dest = control.setting('movie.download.path')
            dest = control.transPath(dest)
            for level in levels:
                try: control.makeFile(os.path.abspath(os.path.join(dest, level)))
                except: pass
            control.makeFile(dest)
            dest = os.path.join(dest, transname)
            control.makeFile(dest)
            ext = os.path.splitext(urlparse.urlparse(url).path)[1][1:]
            if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']: ext = 'mp4'
            dest = os.path.join(dest, transname + '.' + ext)
        else: #Serien
            transname = name.translate(None, '\/:*?"<>|').strip('.')
            content = re.compile('(.+?)\sS(\d*)E\d*$').findall(name)
            transtvshowtitle = content[0][0].translate(None, '\/:*?"<>|').strip('.')
            name = transname
            levels =['../../../..', '../../..', '../..', '..']
            dest = control.setting('tv.download.path')
            dest = control.transPath(dest)
            for level in levels:
                try: control.makeFile(os.path.abspath(os.path.join(dest, level)))
                except: pass
            control.makeFile(dest)
            dest = os.path.join(dest, transtvshowtitle)
            control.makeFile(dest)
            DownloadSeasonName = control.setting('Download.Season.Name')
            if DownloadSeasonName == '0':
                dest = os.path.join(dest, 'Season %01d' % int(content[0][1]))
            else:
                pass
            if DownloadSeasonName == '1':
                dest = os.path.join(dest, 'S%01d' % int(content[0][1]))
            else:
                pass
            if DownloadSeasonName == '2':
                dest = os.path.join(dest, 'Staffel %01d' % int(content[0][1]))
            else:
                pass
            control.makeFile(dest)
            ext = os.path.splitext(urlparse.urlparse(url).path)[1][1:]
            if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']: ext = 'mp4'
            dest = os.path.join(dest, transname + '.' + ext)
            
    sysheaders = urllib.quote_plus(json.dumps(headers))

    sysurl = urllib.quote_plus(url)

    systitle = urllib.quote_plus(name)

    sysimage = urllib.quote_plus(image)

    sysdest = urllib.quote_plus(dest)

    script = inspect.getfile(inspect.currentframe())
    cmd = 'RunScript(%s, %s, %s, %s, %s, %s)' % (script, sysurl, sysdest, systitle, sysimage, sysheaders)

    xbmc.executebuiltin(cmd)


def getResponse(url, headers, size):
    try:
        if size > 0:
            size = int(size)
            headers['Range'] = 'bytes=%d-' % size

        req = urllib2.Request(url, headers=headers)

        resp = urllib2.urlopen(req, timeout=30)
        return resp
    except:
        return None


def done(title, dest, downloaded):
    playing = xbmc.Player().isPlaying()

    text = xbmcgui.Window(10000).getProperty('GEN-DOWNLOADED')

    if len(text) > 0:
        text += '[CR]'

    if downloaded:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR forestgreen]Download erfolgreich[/COLOR]')
    else:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR red]Download fehlgeschlagen[/COLOR]')

    xbmcgui.Window(10000).setProperty('GEN-DOWNLOADED', text)

    if (not downloaded) or (not playing): 
        xbmcgui.Dialog().ok(title, text)
        xbmcgui.Window(10000).clearProperty('GEN-DOWNLOADED')


def doDownload(url, dest, title, image, headers):

    headers = json.loads(urllib.unquote_plus(headers))

    url = urllib.unquote_plus(url)

    title = urllib.unquote_plus(title)

    image = urllib.unquote_plus(image)

    dest = urllib.unquote_plus(dest)

    file = dest.rsplit(os.sep, 1)[-1]

    resp = getResponse(url, headers, 0)

    if not resp:
        xbmcgui.Dialog().ok(title, dest, 'Download fehlgeschlagen', 'Keine Antwort vom Server')
        return

    try:    content = int(resp.headers['Content-Length'])
    except: content = 0

    try:    resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except: resumable = False

    #print "Download Header"
    #print resp.headers
    if resumable:
        print "Download is resumable"

    if content < 1:
        xbmcgui.Dialog().ok(title, file, 'Unbekannte Dateigröße', 'Download nicht möglich')
        return

    size = 1024 * 1024
    mb = content / (1024 * 1024)

    if content < size:
        size = content

    total = 0
    notify = 0
    errors = 0
    count = 0
    resume = 0
    sleep = 0

    if xbmcgui.Dialog().yesno(title + ' - Download bestätigen', file, 'Dateigröße %dMB' % mb, 'Download fortsetzen?', 'Fortsetzen',  'Abbrechen') == 1:
        return

    print 'Download File Size : %dMB %s ' % (mb, dest)

    #f = open(dest, mode='wb')
    f = xbmcvfs.File(dest, 'w')

    chunks = []

    while True:
        downloaded = total
        for c in chunks:
            downloaded += len(c)
        percent = min(100 * downloaded / content, 100)
        if percent >= notify:
            xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i,%s)" % ( str(percent)+'%' + ' - ' + title, dest, 10000, image))

            print 'Download percent : %s %s %dMB downloaded : %sMB File Size : %sMB' % (str(percent)+'%', dest, mb, downloaded / 1000000, content / 1000000)

            notify += 10

        chunk = None
        error = False

        try:        
            chunk = resp.read(size)
            if not chunk:
                if percent < 99:
                    error = True
                else:
                    while len(chunks) > 0:
                        c = chunks.pop(0)
                        f.write(c)
                        del c

                    f.close()
                    print '%s download complete' % (dest)
                    return done(title, dest, True)

        except Exception, e:
            print str(e)
            error = True
            sleep = 10
            errno = 0

            if hasattr(e, 'errno'):
                errno = e.errno

            if errno == 10035: # 'A non-blocking socket operation could not be completed immediately'
                pass

            if errno == 10054: #'An existing connection was forcibly closed by the remote host'
                errors = 10 #force resume
                sleep  = 30

            if errno == 11001: # 'getaddrinfo failed'
                errors = 10 #force resume
                sleep  = 30

        if chunk:
            errors = 0
            chunks.append(chunk)
            if len(chunks) > 5:
                c = chunks.pop(0)
                f.write(c)
                total += len(c)
                del c

        if error:
            errors += 1
            count  += 1
            print '%d Error(s) whilst downloading %s' % (count, dest)
            xbmc.sleep(sleep*1000)

        if (resumable and errors > 0) or errors >= 10:
            if (not resumable and resume >= 50) or resume >= 500:
                #Give up!
                print '%s download canceled - too many error whilst downloading' % (dest)
                return done(title, dest, False)

            resume += 1
            errors  = 0
            if resumable:
                chunks  = []
                #create new response
                print 'Download resumed (%d) %s' % (resume, dest)
                resp = getResponse(url, headers, total)
            else:
                #use existing response
                pass


if __name__ == '__main__':
    if 'downloader.py' in sys.argv[0]:
        doDownload(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
