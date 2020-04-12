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

import sys,re,json,urllib,urlparse,random,datetime,time,xbmcaddon

from resources.lib.modules import trakt
from resources.lib.modules import tvmaze
from resources.lib.modules import cache
from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import debrid
from resources.lib.modules import workers
from resources.lib.modules import source_utils
from resources.lib.modules import log_utils
from resources.lib.modules import source_faultlog

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

try: import urlresolver
except: pass

try: import xbmc
except: pass

this_addon =  xbmcaddon.Addon()

class sources:
    def __init__(self):
        self.getConstants()
        self.sources = []

    def play(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, meta, select, preload=False):
        try:
            url = None
            control.moderator()
            if preload == False:
                items = self.getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
            else:
                items = self.getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, preload=True)

            select = control.setting('hosts.mode') if select == None else select

            title = tvshowtitle if not tvshowtitle == None else title

            if control.window.getProperty('PseudoTVRunning') == 'True':
                return control.resolve(int(sys.argv[1]), True, control.item(path=str(self.sourcesDirect(items))))

            if len(items) > 0:

                if select == '1' and 'plugin' in control.infoLabel('Container.PluginName'):

                    control.window.clearProperty(self.itemProperty)
                    control.window.setProperty(self.itemProperty, json.dumps(items))
                    
                    control.window.clearProperty(self.metaProperty)
                    control.window.setProperty(self.metaProperty, meta)

                    control.sleep(200)

                    if preload == False:
                        return control.execute('Container.Update(%s?action=addItem&title=%s)' % (sys.argv[0], urllib.quote_plus(title)))
                elif select == '0' or select == '1':
                    if preload == False:
                        url = self.sourcesDialog(items)

                else:
                    url = self.sourcesDirect(items)

            if preload == False:
                if url == None:      
                    return self.errorForSources()

            try: meta = json.loads(meta)
            except: pass
            if preload == False:
                from resources.lib.modules.player import player
                player().run(title, year, season, episode, imdb, tvdb, url, meta)
            else:
                control.infoDialog("Preload fertig", sound=False, icon='INFO')
        except:
            pass


    def addItem(self, title):
        control.playlist.clear()

        items = control.window.getProperty(self.itemProperty)
        items = json.loads(items)

        if items == None or len(items) == 0: control.idle() ; sys.exit()

        meta = control.window.getProperty(self.metaProperty)
        meta = json.loads(meta)

        # (Kodi bug?) [name,role] is incredibly slow on this directory, [name] is barely tolerable, so just nuke it for speed!
        if 'cast' in meta: del(meta['cast'])

        sysaddon = sys.argv[0]

        syshandle = int(sys.argv[1])

        downloads = True if control.setting('downloads') == 'true' and not (control.setting('movie.download.path') == '' or control.setting('tv.download.path') == '') else False

        systitle = sysname = urllib.quote_plus(title)

        if 'tvshowtitle' in meta and 'season' in meta and 'episode' in meta:
            sysname += urllib.quote_plus(' S%02dE%02d' % (int(meta['season']), int(meta['episode'])))
        elif 'year' in meta:
            sysname += urllib.quote_plus(' (%s)' % meta['year'])

        ## Fanart Feature problematik - hier wird db item übergeben, aber nicht die auswahl ##
        ## GGf. sollte man überlegen, die Auswahl in meta.items reinzuschreiben

        poster = json.dumps(meta['poster3']) if 'poster3' in meta else '0'
        if poster == '0': poster = json.dumps(meta['poster']) if 'poster' in meta else '0'

        poster=json.loads(poster)[0]

        fanart = json.dumps(meta['fanart2']) if 'fanart2' in meta else '0'
        if fanart == '0': fanart = json.dumps(meta['fanart']) if 'fanart' in meta else '0'

        fanart=json.loads(fanart)[0]

        ## /Fanart Feature problematik ##

        thumb = meta['thumb'] if 'thumb' in meta else '0'
        if thumb == '0': thumb = poster
        if thumb == '0': thumb = fanart

        banner = meta['banner'] if 'banner' in meta else '0'
        if banner == '0': banner = poster

        if poster == '0': poster = control.addonPoster()
        if banner == '0': banner = control.addonBanner()
        if not control.setting('fanart') == 'true': fanart = '0'
        if fanart == '0': fanart = control.addonFanart()
        if thumb == '0': thumb = control.addonFanart()

        sysimage = urllib.quote_plus(poster.encode('utf-8'))

        for i in range(len(items)):
            try:
                label = items[i]['label']

                syssource = urllib.quote_plus(json.dumps([items[i]]))

                sysurl = '%s?action=playItem&title=%s&source=%s' % (sysaddon, systitle, syssource)

                cm = []

                if downloads == True:
                    cm.append(("Download", 'RunPlugin(%s?action=download&name=%s&image=%s&source=%s)' % (sysaddon, sysname, sysimage, syssource)))

                item = control.item(label=label)

                item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'banner': banner})

                item.setProperty('Fanart_Image', fanart)

                video_streaminfo = {'codec': 'h264'}
                item.addStreamInfo('video', video_streaminfo)

                item.addContextMenuItems(cm)
                
                meta.pop('fanart2', None)
                meta.pop('imdb', None)
                meta.pop('metacache', None)
                meta.pop('next', None)
                meta.pop('poster3', None)
                meta.pop('tmdb', None)
                meta.pop('tmdb_id', None)
                meta.pop('poster', None)
                meta.pop('banner', None)
                meta.pop('tvdb', None)
                meta.pop('tvdb_id', None)
                meta.pop('fanart', None)
                meta.pop('imdb_id', None)
                meta.pop('label', None)
                meta.pop('thumb', None)
                meta.pop('unaired', None)
                
                item.setInfo(type='Video', infoLabels= meta)

                ## Notwendig für Library Exporte ##

                ## Amazon Scraper Details ##
                if "amazon" in label.lower():
                    item.setProperty('IsPlayable', 'true')
                    aid=re.search(r'asin%3D(.*?)%22%2C', sysurl)
                    if control.setting('provider.amazonapp') == '0':
                        sysurl='plugin://plugin.video.amazon-test/?mode=PlayVideo&asin=' + aid.group(1)
                    if control.setting('provider.amazonapp') == '1':
                        sysurl='plugin://plugin.video.amazon/?sitemode=PLAYVIDEO&mode=play&asin=' + aid.group(1)


                ## Netflix Scraper Details ##
                if "netflix" in label.lower():
                    item.setProperty('IsPlayable', 'true')
                    aid=re.search(r'video_id%3D(.*?)%22%2C', sysurl)
                    sysurl='plugin://plugin.video.netflix/?action=play_video&video_id=' + aid.group(1)


                ## Maxdome Scraper Details ##
                if "maxdome" in label.lower():
                    item.setProperty('IsPlayable', 'true')
                    aid=re.search(r'id%3D(.*?)%22%2C', sysurl)
                    sysurl='plugin://plugin.video.maxdome/?action=play&id=' + aid.group(1)


                control.addItem(handle=syshandle, url=sysurl, listitem=item, isFolder=False)
            except:
                pass

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=True)


    def playItem(self, title, source):
        try:
            meta = control.window.getProperty(self.metaProperty)
            meta = json.loads(meta)

            year = meta['year'] if 'year' in meta else None
            season = meta['season'] if 'season' in meta else None
            episode = meta['episode'] if 'episode' in meta else None

            imdb = meta['imdb'] if 'imdb' in meta else None
            tvdb = meta['tvdb'] if 'tvdb' in meta else None

            next = [] ; prev = [] ; total = []
            for i in range(1,1000):
                try:
                    u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
                    if u in total: raise Exception()
                    total.append(u)
                    u = dict(urlparse.parse_qsl(u.replace('?','')))
                    u = json.loads(u['source'])[0]
                    next.append(u)
                except:
                    break
            for i in range(-1000,0)[::-1]:
                try:
                    u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
                    if u in total: raise Exception()
                    total.append(u)
                    u = dict(urlparse.parse_qsl(u.replace('?','')))
                    u = json.loads(u['source'])[0]
                    prev.append(u)
                except:
                    break

            items = json.loads(source)
            items = [i for i in items+next+prev][:40]
            header = control.addonInfo('name')
            header2 = header.upper()

            progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
            progressDialog.create(header, '')
            progressDialog.update(0)

            block = None
            for i in range(len(items)):
                try:
                    try:
                        if progressDialog.iscanceled(): break
                        progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
                    except:
                        progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))

                    if items[i]['source'] == block: raise Exception()
                    w = workers.Thread(self.sourcesResolve, items[i])
                    w.start()

                    offset = 60 * 2 if items[i].get('source') in self.hostpairDict else 0

                    waiting_time = 30
                    while waiting_time > 0:
                        try:
                            if xbmc.abortRequested == True: return sys.exit()
                            if progressDialog.iscanceled(): return progressDialog.close()
                        except:
                            pass

                        if w.is_alive() == False: break
                        time.sleep(0.5)

                        waiting_time = waiting_time - 0.5
                        if control.condVisibility('Window.IsActive(virtualkeyboard)') or \
                                control.condVisibility('Window.IsActive(yesnoDialog)') or \
                                control.condVisibility('Window.IsActive(PopupRecapInfoWindow)') or \
                                control.condVisibility('Window.IsActive(ProgressDialog)'):
                            waiting_time = waiting_time + 0.5 #dont count down while dialog is presented

                    if w.is_alive() == True: block = items[i]['source']

                    if self.url == None:
                        if items[i]['source'] == "fast.streamservice.online":
                            w.join(5000)
                            if self.url == None:
                                raise Exception()
                        else:
                            raise Exception()

                    try: progressDialog.close()
                    except: pass

                    control.sleep(200)
                    control.execute('Dialog.Close(virtualkeyboard)')
                    control.execute('Dialog.Close(yesnoDialog)')

                    from resources.lib.modules.player import player
                    player().run(title, year, season, episode, imdb, tvdb, self.url, meta)

                    return self.url
                except:
                    pass

            try: progressDialog.close()
            except: pass

            self.errorForSources()
        except:
            pass

    def getSources(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, quality='HD', timeout=30, preload=False):

        if preload == False:
            progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
            progressDialog.create(control.addonInfo('name'), '')
            progressDialog.update(0)

        self.prepareSources()

        sourceDict = self.sourceDict

        if this_addon.getSetting('hosts.mode') == '2' and this_addon.getSetting('autoplay.mode') == 'true':
            if preload == False:
                progressDialog.update(0, "Bitte warten")
        else:
            if preload == False:
                progressDialog.update(0, "Quellen werden vorbereitet")

        content = 'movie' if tvshowtitle == None else 'episode'
        if content == 'movie':
            sourceDict = [(i[0], i[1], getattr(i[1], 'movie', None)) for i in sourceDict]
            genres = trakt.getGenre('movie', 'imdb', imdb)
        else:
            sourceDict = [(i[0], i[1], getattr(i[1], 'tvshow', None)) for i in sourceDict]
            genres = trakt.getGenre('show', 'tvdb', tvdb)

        sourceDict = [(i[0], i[1], i[2]) for i in sourceDict if not hasattr(i[1], 'genre_filter') or not i[1].genre_filter or any(x in i[1].genre_filter for x in genres)]
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] == None]

        language = self.getLanguage()
        sourceDict = [(i[0], i[1], i[1].language) for i in sourceDict]
        sourceDict = [(i[0], i[1]) for i in sourceDict if any(x in i[2] for x in language)]


        try: sourceDict = [(i[0], i[1], control.setting('provider.' + i[0])) for i in sourceDict]
        except: sourceDict = [(i[0], i[1], 'true') for i in sourceDict]
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] == 'false']

        try: faultLoggerEnable = control.setting('FaultLogger.enabled')
        except: faultLoggerEnable = "false"
        if faultLoggerEnable == 'true':
            source_faultlog.init()
            sourceDict = [(i[0], i[1]) for i in sourceDict if source_faultlog.isEnabled(i[0])]

        sourceDict = [(i[0], i[1], i[1].priority) for i in sourceDict]

        random.shuffle(sourceDict)
        sourceDict = sorted(sourceDict, key=lambda i: i[2])

        threads = []

        if content == 'movie':
            title = self.getTitle(title)
            localtitle = self.getLocalTitle(title, imdb, tvdb, content)
            aliases = self.getAliasTitles(imdb, localtitle, content)
            for i in sourceDict: threads.append(workers.Thread(self.getMovieSource, title, localtitle, aliases, year, imdb, i[0], i[1]))
        else:
            tvshowtitle = self.getTitle(tvshowtitle)
            localtvshowtitle = self.getLocalTitle(tvshowtitle, imdb, tvdb, content)
            aliases = self.getAliasTitles(imdb, localtvshowtitle, content)
            #Disabled on 11/11/17 due to hang. Should be checked in the future and possible enabled again.
            for i in sourceDict: threads.append(workers.Thread(self.getEpisodeSource, title, year, imdb, tvdb, season, episode, tvshowtitle, localtvshowtitle, aliases, premiered, i[0], i[1]))

        s = [i[0] + (i[1],) for i in zip(sourceDict, threads)]
        s = [(i[3].getName(), i[0], i[2]) for i in s]

        mainsourceDict = [i[0] for i in s if i[2] == 0]
        sourcelabelDict = dict([(i[0], i[1].upper()) for i in s])

        [i.start() for i in threads]

        string3 = "Verbleibende Indexseiten: %s"
        string4 = "Total"

        string6 = "Prem"
        string7 = "Normal"

        try: timeout = int(control.setting('scrapers.timeout.1'))
        except: pass

        quality = control.setting('hosts.quality')
        if quality == '': quality = '0'

        line1 = line2 = ""

        pre_emp = control.setting('preemptive.termination')
        pre_emp_limit = control.setting('preemptive.limit')

        source_4k = d_source_4k = 0
        source_1080 = d_source_1080 = 0
        source_720 = d_source_720 = 0
        source_sd = d_source_sd = 0
        total = d_total = 0

        debrid_list = debrid.debrid_resolvers
        debrid_status = debrid.status()

        total_format = '[COLOR %s][B]%s[/B][/COLOR]'
        pdiag_format = ' 4K: %s | 1080p: %s | 720p: %s | SD: %s | %s: %s'.split('|')
        pdiag_bg_format = '4K:%s(%s)|1080p:%s(%s)|720p:%s(%s)|SD:%s(%s)|T:%s(%s)'.split('|')

        for i in range(0, 4 * timeout):
            if str(pre_emp) == 'true':
                if quality in ['1','0']:
                    if (source_1080 + d_source_1080) >= int(pre_emp_limit): break
                elif quality in ['2']:
                    if (source_720 + d_source_720) >= int(pre_emp_limit): break
                elif quality in ['3']:
                    if (source_sd + d_source_sd) >= int(pre_emp_limit): break
                else:
                    if (source_sd + d_source_sd) >= int(pre_emp_limit): break
            try:
                if xbmc.abortRequested == True: return sys.exit()
                try:
                    if preload == False:
                        if progressDialog.iscanceled(): break
                except:
                    pass

                if len(self.sources) > 0:
                    if quality in ['0']:
                        source_4k = len([e for e in self.sources if e['quality'] == '4K' and e['debridonly'] == False])
                        source_1080 = len([e for e in self.sources if e['quality'] in ['1440p','1080p'] and e['debridonly'] == False])
                        source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and e['debridonly'] == False])
                        source_sd = len([e for e in self.sources if e['quality'] == 'SD' and e['debridonly'] == False])
                    elif quality in ['1']:
                        source_1080 = len([e for e in self.sources if e['quality'] in ['1440p','1080p'] and e['debridonly'] == False])
                        source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and e['debridonly'] == False])
                        source_sd = len([e for e in self.sources if e['quality'] == 'SD' and e['debridonly'] == False])
                    elif quality in ['2']:
                        source_1080 = len([e for e in self.sources if e['quality'] in ['1080p'] and e['debridonly'] == False])
                        source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and e['debridonly'] == False])
                        source_sd = len([e for e in self.sources if e['quality'] == 'SD' and e['debridonly'] == False])
                    elif quality in ['3']:
                        source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and e['debridonly'] == False])
                        source_sd = len([e for e in self.sources if e['quality'] == 'SD' and e['debridonly'] == False])
                    else:
                        source_sd = len([e for e in self.sources if e['quality'] == 'SD' and e['debridonly'] == False])

                    total = source_4k + source_1080 + source_720 + source_sd

                    if debrid_status:
                        if quality in ['0']:
                            for d in debrid_list:
                                d_source_4k = len([e for e in self.sources if e['quality'] == '4K' and d.valid_url('', e['source'])])
                                d_source_1080 = len([e for e in self.sources if e['quality'] in ['1440p','1080p'] and d.valid_url('', e['source'])])
                                d_source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and d.valid_url('', e['source'])])
                                d_source_sd = len([e for e in self.sources if e['quality'] == 'SD' and d.valid_url('', e['source'])])
                        elif quality in ['1']:
                            for d in debrid_list:
                                d_source_1080 = len([e for e in self.sources if e['quality'] in ['1440p','1080p'] and d.valid_url('', e['source'])])
                                d_source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and d.valid_url('', e['source'])])
                                d_source_sd = len([e for e in self.sources if e['quality'] == 'SD' and d.valid_url('', e['source'])])
                        elif quality in ['2']:
                            for d in debrid_list:
                                d_source_1080 = len([e for e in self.sources if e['quality'] in ['1080p'] and d.valid_url('', e['source'])])
                                d_source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and d.valid_url('', e['source'])])
                                d_source_sd = len([e for e in self.sources if e['quality'] == 'SD' and d.valid_url('', e['source'])])
                        elif quality in ['3']:
                            for d in debrid_list:
                                d_source_720 = len([e for e in self.sources if e['quality'] in ['720p','HD'] and d.valid_url('', e['source'])])
                                d_source_sd = len([e for e in self.sources if e['quality'] == 'SD' and d.valid_url('', e['source'])])
                        else:
                            for d in debrid_list:
                                d_source_sd = len([e for e in self.sources if e['quality'] == 'SD' and d.valid_url('', e['source'])])

                        d_total = d_source_4k + d_source_1080 + d_source_720 + d_source_sd

                if debrid_status:
                    d_4k_label = total_format % ('red', d_source_4k) if d_source_4k == 0 else total_format % ('lime', d_source_4k)
                    d_1080_label = total_format % ('red', d_source_1080) if d_source_1080 == 0 else total_format % ('lime', d_source_1080)
                    d_720_label = total_format % ('red', d_source_720) if d_source_720 == 0 else total_format % ('lime', d_source_720)
                    d_sd_label = total_format % ('red', d_source_sd) if d_source_sd == 0 else total_format % ('lime', d_source_sd)
                    d_total_label = total_format % ('red', d_total) if d_total == 0 else total_format % ('lime', d_total)

                source_4k_label = total_format % ('red', source_4k) if source_4k == 0 else total_format % ('lime', source_4k)
                source_1080_label = total_format % ('red', source_1080) if source_1080 == 0 else total_format % ('lime', source_1080)
                source_720_label = total_format % ('red', source_720) if source_720 == 0 else total_format % ('lime', source_720)
                source_sd_label = total_format % ('red', source_sd) if source_sd == 0 else total_format % ('lime', source_sd)
                source_total_label = total_format % ('red', total) if total == 0 else total_format % ('lime', total)
                if preload == False:
                    if (i / 2) < timeout:
                        try:
                            mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() == True and x.getName() in mainsourceDict]
                            info = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() == True]
                            if i >= timeout and len(mainleft) == 0 and len(self.sources) >= 100 * len(info): break # improve responsiveness
                            if debrid_status:
                                if quality in ['0']:
                                    if not progressDialog == control.progressDialogBG:
                                        line1 = ('%s:' + '|'.join(pdiag_format)) % (string6, d_4k_label, d_1080_label, d_720_label, d_sd_label, str(string4), d_total_label)
                                        line2 = ('%s:' + '|'.join(pdiag_format)) % (string7, source_4k_label, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
                                    else:
                                        line1 = '|'.join(pdiag_bg_format[:-1]) % (source_4k_label, d_4k_label, source_1080_label, d_1080_label, source_720_label, d_720_label, source_sd_label, d_sd_label)
                                elif quality in ['1']:
                                    if not progressDialog == control.progressDialogBG:
                                        line1 = ('%s:' + '|'.join(pdiag_format[1:])) % (string6, d_1080_label, d_720_label, d_sd_label, str(string4), d_total_label)
                                        line2 = ('%s:' + '|'.join(pdiag_format[1:])) % (string7, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
                                    else:
                                        line1 = '|'.join(pdiag_bg_format[1:]) % (source_1080_label, d_1080_label, source_720_label, d_720_label, source_sd_label, d_sd_label, source_total_label, d_total_label)
                                elif quality in ['2']:
                                    if not progressDialog == control.progressDialogBG:
                                        line1 = ('%s:' + '|'.join(pdiag_format[1:])) % (string6, d_1080_label, d_720_label, d_sd_label, str(string4), d_total_label)
                                        line2 = ('%s:' + '|'.join(pdiag_format[1:])) % (string7, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
                                    else:
                                        line1 = '|'.join(pdiag_bg_format[1:]) % (source_1080_label, d_1080_label, source_720_label, d_720_label, source_sd_label, d_sd_label, source_total_label, d_total_label)
                                elif quality in ['3']:
                                    if not progressDialog == control.progressDialogBG:
                                        line1 = ('%s:' + '|'.join(pdiag_format[2:])) % (string6, d_720_label, d_sd_label, str(string4), d_total_label)
                                        line2 = ('%s:' + '|'.join(pdiag_format[2:])) % (string7, source_720_label, source_sd_label, str(string4), source_total_label)
                                    else:
                                        line1 = '|'.join(pdiag_bg_format[2:]) % (source_720_label, d_720_label, source_sd_label, d_sd_label, source_total_label, d_total_label)
                                else:
                                    if not progressDialog == control.progressDialogBG:
                                        line1 = ('%s:' + '|'.join(pdiag_format[3:])) % (string6, d_sd_label, str(string4), d_total_label)
                                        line2 = ('%s:' + '|'.join(pdiag_format[3:])) % (string7, source_sd_label, str(string4), source_total_label)
                                    else:
                                        line1 = '|'.join(pdiag_bg_format[3:]) % (source_sd_label, d_sd_label, source_total_label, d_total_label)
                            else:
                                if quality in ['0']:
                                    line1 = '|'.join(pdiag_format) % (source_4k_label, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
                                elif quality in ['1']:
                                    line1 = '|'.join(pdiag_format[1:]) % (source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
                                elif quality in ['2']:
                                    line1 = '|'.join(pdiag_format[1:]) % (source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
                                elif quality in ['3']:
                                    line1 = '|'.join(pdiag_format[2:]) % (source_720_label, source_sd_label, str(string4), source_total_label)
                                else:
                                    line1 = '|'.join(pdiag_format[3:]) % (source_sd_label, str(string4), source_total_label)

                            if debrid_status:
                                if this_addon.getSetting('hosts.mode') == '2' and this_addon.getSetting('autoplay.mode') == 'true':
                                    line2 = ''
                                    line1 = ''
                                else:
                                    if len(info) > 6: line3 = string3 % (str(len(info)))
                                    elif len(info) > 0: line3 = string3 % (', '.join(info))
                                    else: break

                                percent = int(100 * float(i) / (2 * timeout) + 0.5)
                                if not progressDialog == control.progressDialogBG: progressDialog.update(max(1, percent), line1, line2, line3)
                                else: progressDialog.update(max(1, percent), line1, line3)
                            else:
                                if this_addon.getSetting('hosts.mode') == '2' and this_addon.getSetting('autoplay.mode') == 'true':
                                    line2 = ''
                                    line1 = ''
                                else:
                                    if len(info) > 6: line2 = string3 % (str(len(info)))
                                    elif len(info) > 0: line2 = string3 % (', '.join(info))
                                    else: break

                                percent = int(100 * float(i) / (2 * timeout) + 0.5)
                                progressDialog.update(max(1, percent), line1, line2)
                        except Exception as e:
                            log_utils.log('Exception Raised: %s' % str(e), log_utils.LOGERROR)
                    else:
                        try:
                            mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() == True and x.getName() in mainsourceDict]
                            info = mainleft
                            if debrid_status:
                                if len(info) > 6: line3 = 'Waiting for: %s' % (str(len(info)))
                                elif len(info) > 0: line3 = 'Waiting for: %s' % (', '.join(info))
                                else: break
                                percent = int(100 * float(i) / (2 * timeout) + 0.5) % 100
                                if not progressDialog == control.progressDialogBG: progressDialog.update(max(1, percent), line1, line2, line3)
                                else: progressDialog.update(max(1, percent), line1, line3)
                            else:
                                if len(info) > 6: line2 = 'Waiting for: %s' % (str(len(info)))
                                elif len(info) > 0: line2 = 'Waiting for: %s' % (', '.join(info))
                                else: break
                                percent = int(100 * float(i) / (2 * timeout) + 0.5) % 100
                                progressDialog.update(max(1, percent), line1, line2)
                        except:
                            break

                time.sleep(0.5)
            except:
                pass

        try:
            if preload == False:
                progressDialog.close()
        except: pass

        self.sourcesFilter()

        return self.sources

    def prepareSources(self):
        try:
            control.makeFile(control.dataPath)

            self.sourceFile = control.providercacheFile

            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
            dbcur.execute("CREATE TABLE IF NOT EXISTS rel_url (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""rel_url TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
            dbcur.execute("CREATE TABLE IF NOT EXISTS rel_src (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""hosts TEXT, ""added TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
        except:
            pass


    def getMovieSource(self, title, localtitle, aliases, year, imdb, source, call):
    ## Note: Kein Provider Cache fuer Emby. Siehe --> if not "emby" in source:
        try:
            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
        except:
            pass

        ''' Fix to stop items passed with a 0 IMDB id pulling old unrelated sources from the database. '''
        if imdb == '0':
            try:
                dbcur.execute("DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
                dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
                dbcon.commit()
            except:
                pass
        ''' END '''

        try:
            dbcur.execute("SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            match = dbcur.fetchone()
            t1 = int(re.sub('[^0-9]', '', str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            update = abs(t2 - t1) > 60
            if update == False:
                sources = eval(match[4].encode('utf-8'))
                return self.sources.extend(sources)
        except:
            pass

        try:
            url = None
            dbcur.execute("SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            url = dbcur.fetchone()
            url = eval(url[4].encode('utf-8'))
        except:
            pass

        try:
            if url == None: url = call.movie(imdb, title, localtitle, aliases, year)
            if url == None: raise Exception()
            dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            if not "emby" in source:dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
            dbcon.commit()
        except:
            pass

        try:
            sources = call.sources(url, self.hostDict, self.hostprDict)
            if sources == None or sources == []: raise Exception()
            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            for i in sources: i.update({'provider': source})
            self.sources.extend(sources)
            dbcur.execute("DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            if not "emby" in source:dbcur.execute("INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '', '', repr(sources), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            dbcon.commit()
        except:
            pass


    def getEpisodeSource(self, title, year, imdb, tvdb, season, episode, tvshowtitle, localtvshowtitle, aliases, premiered, source, call):
        try:
            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
        except:
            pass

        try:
            dbcur.execute("SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            match = dbcur.fetchone()
            t1 = int(re.sub('[^0-9]', '', str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            update = abs(t2 - t1) > 60
            if update == False:
                sources = eval(match[4].encode('utf-8'))
                return self.sources.extend(sources)
        except:
            pass

        try:
            url = None
            dbcur.execute("SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            url = dbcur.fetchone()
            url = eval(url[4].encode('utf-8'))
        except:
            pass

        try:
            if url == None: url = call.tvshow(imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year)
            if url == None: raise Exception()
            dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
            dbcon.commit()
        except:
            pass

        try:
            ep_url = None
            dbcur.execute("SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            ep_url = dbcur.fetchone()
            ep_url = eval(ep_url[4].encode('utf-8'))
        except:
            pass

        try:
            if url == None: raise Exception()
            if ep_url == None: ep_url = call.episode(url, imdb, tvdb, title, premiered, season, episode)
            if ep_url == None: raise Exception()
            dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(ep_url)))
            dbcon.commit()
        except:
            pass

        try:
            sources = call.sources(ep_url, self.hostDict, self.hostprDict)
            if sources == None or sources == []: raise Exception()
            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            for i in sources: i.update({'provider': source})
            self.sources.extend(sources)
            dbcur.execute("DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            dbcur.execute("INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(sources), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            dbcon.commit()
        except:
            pass


    def alterSources(self, url, meta):
        try:
            if control.setting('hosts.mode') == '2': url += '&select=1'
            else: url += '&select=2'
            control.execute('RunPlugin(%s)' % url)
        except:
            pass


    def clearSources(self):
        try:
            control.idle()

            if control.yesnoDialog("Sind Sie sicher?", '', ''):
                cache.cache_clear_providers()
                control.infoDialog("Vorgang abgeschlossen", sound=True, icon='INFO')
        except:
            pass

    def sourcesFilter(self):
        provider = control.setting('hosts.sort.provider')
        if provider == '': provider = 'false'

        no_subbed = control.setting('no.subbed')
        if no_subbed == '': no_subbed = 'false'

        quality = control.setting('hosts.quality')
        if quality == '': quality = '0'

        pairing = control.setting('hosts.pairing')
        if pairing == '': pairing = 'true'

        blocking = control.setting('hosts.blocking')
        if blocking == '': blocking = 'false'


        HEVC = control.setting('HEVC')

        random.shuffle(self.sources)

        if provider == 'true':
            self.sources = sorted(self.sources, key=lambda k: k['provider'])

        for i in self.sources:
            if 'checkquality' in i and i['checkquality'] == True:
                if not i['source'].lower() in self.hosthqDict and i['quality'] not in ['SD', 'SCR', 'CAM']: i.update({'quality': 'SD'})

        local = [i for i in self.sources if 'local' in i and i['local'] == True]

        ## quick & drity fix,sor if multiple available items with different quality
        ## https://github.com/lastship/plugin.video.lastship/issues/119
        local = sorted(local, key=lambda k: k['quality'],reverse=True)
        ## END ##
        
        for i in local: i.update({'language': self._getPrimaryLang() or 'de'})
        self.sources = [i for i in self.sources if not i in local]

        filter = []
        filter += [i for i in self.sources if i['direct'] == True]
        filter += [i for i in self.sources if i['direct'] == False]
        self.sources = filter

        filter = []


        for d in debrid.debrid_resolvers:
            valid_hoster = set([i['source'] for i in self.sources])
            valid_hoster = [i for i in valid_hoster if d.valid_url('', i)]
            filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster]

        #removing debrid only function, re-use for  https://github.com/lastship/plugin.video.lastship/issues/120
        ## debrid_only wird zu no_subbed
        #if debrid_only == 'false' or  debrid.status() == False:
        filter += [i for i in self.sources if not i['source'].lower() in self.hostprDict and i['debridonly'] == False]

        self.sources = filter

        for i in range(len(self.sources)):
            q = self.sources[i]['quality']
            if q == 'HD': self.sources[i].update({'quality': '720p'})

        filter = []
        filter += local

        if quality in ['0']: filter += [i for i in self.sources if i['quality'] == '4K' and 'debrid' in i]
        if quality in ['0']: filter += [i for i in self.sources if i['quality'] == '4K' and not 'debrid' in i and 'memberonly' in i]
        if quality in ['0']: filter += [i for i in self.sources if i['quality'] == '4K' and not 'debrid' in i and not 'memberonly' in i]

        if quality in ['0', '1']: filter += [i for i in self.sources if i['quality'] == '1440p' and 'debrid' in i]
        if quality in ['0', '1']: filter += [i for i in self.sources if i['quality'] == '1440p' and not 'debrid' in i and 'memberonly' in i]
        if quality in ['0', '1']: filter += [i for i in self.sources if i['quality'] == '1440p' and not 'debrid' in i and not 'memberonly' in i]

        if quality in ['0', '1', '2']: filter += [i for i in self.sources if i['quality'] == '1080p' and 'debrid' in i]
        if quality in ['0', '1', '2']: filter += [i for i in self.sources if i['quality'] == '1080p' and not 'debrid' in i and 'memberonly' in i]
        if quality in ['0', '1', '2']: filter += [i for i in self.sources if i['quality'] == '1080p' and not 'debrid' in i and not 'memberonly' in i]

        if quality in ['0', '1', '2', '3']: filter += [i for i in self.sources if i['quality'] == '720p' and 'debrid' in i]
        if quality in ['0', '1', '2', '3']: filter += [i for i in self.sources if i['quality'] == '720p' and not 'debrid' in i and 'memberonly' in i]
        if quality in ['0', '1', '2', '3']: filter += [i for i in self.sources if i['quality'] == '720p' and not 'debrid' in i and not 'memberonly' in i]

        filter += [i for i in self.sources if i['quality'] in ['SD', 'SCR', 'CAM']]
        self.sources = filter

        if not pairing == 'true':
            filter = [i for i in self.sources if i['source'].lower() in self.hostpairDict and not 'debrid' in i]
            self.sources = [i for i in self.sources if not i in filter]

        if not blocking == 'false':
            filter = [i for i in self.sources if i['source'].lower() in self.hostblockingDict and not 'debrid' in i]
            self.sources = [i for i in self.sources if not i in filter]

        #removing debrid only function, re-use for  https://github.com/lastship/plugin.video.lastship/issues/120
        if no_subbed == 'true':
            filter = [i for i in self.sources if  'info' in i and 'subbed' in i['info']]
            self.sources = [i for i in self.sources if not i in filter]

        multi = [i['language'] for i in self.sources]
        multi = [x for y,x in enumerate(multi) if x not in multi[:y]]
        multi = True if len(multi) > 1 else False

        if multi == True:
            self.sources = [i for i in self.sources if not i['language'] == 'de'] + [i for i in self.sources if i['language'] == 'en']

        self.sources = self.sources[:2000]

        extra_info = control.setting('sources.extrainfo')
        prem_identify = control.setting('prem.identify')
        if prem_identify == '': prem_identify = 'blue'
        prem_identify = self.getPremColor(prem_identify)

        for i in range(len(self.sources)):

            if extra_info == 'true': t = source_utils.getFileType(self.sources[i]['url'])
            else: t = None

            p = self.sources[i]['provider']

            q = self.sources[i]['quality']

            s = self.sources[i]['source']

            s = s.rsplit('.', 1)[0]

            l = self.sources[i]['language']

            try: f = (' | '.join(['[I]%s [/I]' % info.strip() for info in self.sources[i]['info'].split('|')]))
            except: f = ''

            try: d = self.sources[i]['debrid']
            except: d = self.sources[i]['debrid'] = ''

            if d.lower() == 'real-debrid': d = 'RD'

            if not d == '': label = '%02d | [B]%s | %s[/B] | ' % (int(i+1), d, p)
            else: label = '%02d | [B]%s[/B] | ' % (int(i+1), p)

            if multi == True and not l == 'en': label += '[B]%s[/B] | ' % l

            if t:
                if q in ['4K', '1440p', '1080p', '720p']: label += '%s | [B][I]%s [/I][/B] | [I]%s[/I] | %s' % (s, q, t, f)
                elif q == 'SD': label += '%s | %s | [I]%s[/I]' % (s, f, t)
                else: label += '%s | %s | [I]%s [/I] | [I]%s[/I]' % (s, f, q, t)
            else:
                if q in ['4K', '1440p', '1080p', '720p']: label += '%s | [B][I]%s [/I][/B] | %s' % (s, q, f)
                elif q == 'SD': label += '%s | %s' % (s, f)
                else: label += '%s | %s | [I]%s [/I]' % (s, f, q)
            label = label.replace('| 0 |', '|').replace(' | [I]0 [/I]', '')
            label = re.sub('\[I\]\s+\[/I\]', ' ', label)
            label = re.sub('\|\s+\|', '|', label)
            label = re.sub('\|(?:\s+|)$', '', label)

            if d:
                if not prem_identify == 'nocolor':
                    self.sources[i]['label'] = ('[COLOR %s]' % (prem_identify)) + label.upper() + '[/COLOR]'
                else: self.sources[i]['label'] = label.upper()
            else: self.sources[i]['label'] = label.upper()

            ## EMBY shown as premium link ##
            if (self.sources[i]['provider']=="emby"
                or self.sources[i]['provider']=="amazon"
                or self.sources[i]['provider']=="netflix"
                or self.sources[i]['provider']=="netzkino"
                or self.sources[i]['provider']=="maxdome"
                or self.sources[i]['provider']=="watchbox"
                    ):
                if not prem_identify == 'nocolor':
                    self.sources[i]['label'] = ('[COLOR %s]' % (prem_identify)) + label.upper() + '[/COLOR]'

        try:
            if not HEVC == 'true': self.sources = [i for i in self.sources if not 'HEVC' in i['label']]
        except: pass

        self.sources = [i for i in self.sources if 'label' in i]

        return self.sources


    def sourcesResolve(self, item, info=False):
        try:
            self.url = None

            url = item['url']

            d = item['debrid'] ; direct = item['direct']
            local = item.get('local', False)
            provider = item['provider']
            call = [i[1] for i in self.sourceDict if i[0] == provider][0]
            if 'pairing' in item and item['pairing']:
                call.setRecapInfo(item['label'])
            url = call.resolve(url)
            if url == None or (not '://' in str(url) and not local): raise Exception()

            if not local:
                url = url[8:] if url.startswith('stack:') else url

                urls = []
                for part in url.split(' , '):
                    u = part
                    if not d == '':
                        part = debrid.resolver(part, d)

                    elif not direct == True:
                        hmf = urlresolver.HostedMediaFile(url=u, include_disabled=True, include_universal=False)
                        if hmf.valid_url() == True: part = hmf.resolve()
                    urls.append(part)

                url = 'stack://' + ' , '.join(urls) if len(urls) > 1 else urls[0]

            if url == False or url == None: raise Exception()

            ext = url.split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
            if ext == 'rar': raise Exception()

            try: headers = url.rsplit('|', 1)[1]
            except: headers = ''
            headers = urllib.quote_plus(headers).replace('%3D', '=') if ' ' in headers else headers
            headers = dict(urlparse.parse_qsl(headers))

            if url.startswith('http') and '.m3u8' in url:
                result = client.request(url.split('|')[0], headers=headers, output='geturl', timeout='20')
                if result == None: raise Exception()

            elif url.startswith('http'):
                result = client.request(url.split('|')[0], headers=headers, output='chunk', timeout='20')
                if result == None: raise Exception()

            self.url = url
            return url
        except:
            if info == True: self.errorForSources()
            return


    def sourcesDialog(self, items):
        try:

            labels = [i['label'] for i in items]

            select = control.selectDialog(labels)
            if select == -1: return 'close://'

            next = [y for x,y in enumerate(items) if x >= select]
            prev = [y for x,y in enumerate(items) if x < select][::-1]

            items = [items[select]]
            items = [i for i in items+next+prev][:40]

            header = control.addonInfo('name')
            header2 = header.upper()

            progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
            progressDialog.create(header, '')
            progressDialog.update(0)

            block = None

            for i in range(len(items)):
                try:
                    if items[i]['source'] == block: raise Exception()

                    w = workers.Thread(self.sourcesResolve, items[i])
                    w.start()

                    try:
                        if progressDialog.iscanceled(): break
                        progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
                    except:
                        progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))

                    waiting_time = 30
                    while waiting_time > 0:
                        try:
                            if xbmc.abortRequested == True: return sys.exit()
                            if progressDialog.iscanceled(): return progressDialog.close()
                        except:
                            pass

                        if w.is_alive() == False: break
                        time.sleep(0.5)

                        waiting_time = waiting_time - 0.5
                        if control.condVisibility('Window.IsActive(virtualkeyboard)') or \
                                control.condVisibility('Window.IsActive(yesnoDialog)') or \
                                control.condVisibility('Window.IsActive(PopupRecapInfoWindow)') or \
                                control.condVisibility('Window.IsActive(ProgressDialog)'):
                            waiting_time = waiting_time + 0.5 #dont count down while dialog is presented

                    if w.is_alive() == True: block = items[i]['source']

                    if self.url == None: raise Exception()

                    self.selectedSource = items[i]['label']

                    try: progressDialog.close()
                    except: pass

                    control.execute('Dialog.Close(virtualkeyboard)')
                    control.execute('Dialog.Close(yesnoDialog)')
                    return self.url
                except:
                    pass

            try: progressDialog.close()
            except: pass

        except Exception as e:
            try: progressDialog.close()
            except: pass
            log_utils.log('Error %s' % str(e), log_utils.LOGNOTICE)


    def sourcesDirect(self, items):
        filter = [i for i in items if i['source'].lower() in self.hostpairDict and i['debrid'] == '']
        items = [i for i in items if not i in filter]

        filter = [i for i in items if i['source'].lower() in self.hostblockDict and i['debrid'] == '']
        items = [i for i in items if not i in filter]

        items = [i for i in items if ('autoplay' in i and i['autoplay'] == True) or not 'autoplay' in i]
        
        AutoQualy = control.setting('autoplay.sd')

        if AutoQualy == '1': #SD
            items = [i for i in items if not i['quality'] in ['4K', '1440p', '1080p', '720p', 'HD']]
        else:
            pass
        if AutoQualy == '2': #HD
            items = [i for i in items if i['quality'] in ['4K', '1440p', '1080p', '720p', 'HD']]
        else:
            pass
        #SD + HD
        
        u = None

        header = control.addonInfo('name')
        header2 = header.upper()

        try:
            control.sleep(1000)

            progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
            progressDialog.create(header, '')
            progressDialog.update(0)
        except:
            pass

        for i in range(len(items)):
            try:
                if progressDialog.iscanceled(): break
                progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
            except:
                progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))

            try:
                if xbmc.abortRequested == True: return sys.exit()

                url = self.sourcesResolve(items[i])
                if u == None: u = url
                if not url == None: break
            except:
                pass

        try: progressDialog.close()
        except: pass

        return u

    def errorForSources(self):
        control.infoDialog("Keine Streams verfügbar", sound=False, icon='INFO')


    def getLanguage(self):
        langDict = {'English': ['en'], 'German': ['de'], 'German+English': ['de','en'], 'French': ['fr'], 'French+English': ['fr', 'en'], 'Portuguese': ['pt'], 'Portuguese+English': ['pt', 'en'], 'Polish': ['pl'], 'Polish+English': ['pl', 'en'], 'Korean': ['ko'], 'Korean+English': ['ko', 'en'], 'Russian': ['ru'], 'Russian+English': ['ru', 'en'], 'Spanish': ['es'], 'Spanish+English': ['es', 'en'], 'Greek': ['gr'], 'Italian': ['it'], 'Italian+English': ['it', 'en'], 'Greek+English': ['gr', 'en']}
        name = control.setting('providers.lang')
        return langDict.get(name, ['en'])


    def getLocalTitle(self, title, imdb, tvdb, content):
        lang = self._getPrimaryLang()
        if not lang:
            return title

        if content == 'movie':
            t = trakt.getMovieTranslation(imdb, lang)
        else:
            t = tvmaze.tvMaze().getTVShowTranslation(tvdb, lang)

        return t or title


    def getAliasTitles(self, imdb, localtitle, content):
        lang = self._getPrimaryLang()

        try:
            t = trakt.getMovieAliases(imdb) if content == 'movie' else trakt.getTVShowAliases(imdb)
            t = [i for i in t if i.get('country', '').lower() in [lang, '', 'de'] and i.get('title', '').lower() != localtitle.lower()]
            return t
        except:
            return []

    def _getPrimaryLang(self):
        langDict = {'English': 'en', 'German': 'de', 'German+English': 'de', 'French': 'fr', 'French+English': 'fr', 'Portuguese': 'pt', 'Portuguese+English': 'pt', 'Polish': 'pl', 'Polish+English': 'pl', 'Korean': 'ko', 'Korean+English': 'ko', 'Russian': 'ru', 'Russian+English': 'ru', 'Spanish': 'es', 'Spanish+English': 'es', 'Italian': 'it', 'Italian+English': 'it', 'Greek': 'gr', 'Greek+English': 'gr'}
        name = control.setting('providers.lang')
        lang = langDict.get(name)
        return lang

    def getTitle(self, title):
        title = cleantitle.normalize(title)
        return title

    def getConstants(self):
        self.itemProperty = 'plugin.video.lastship.container.items'

        self.metaProperty = 'plugin.video.lastship.container.meta'

        from resources.lib.sources import sources

        self.sourceDict = sources()

        try:
            self.hostDict = urlresolver.relevant_resolvers(order_matters=True)
            self.hostDict = [i.domains for i in self.hostDict if not '*' in i.domains]
            self.hostDict = [i.lower() for i in reduce(lambda x, y: x+y, self.hostDict)]
            self.hostDict = [x for y,x in enumerate(self.hostDict) if x not in self.hostDict[:y]]
        except:
            self.hostDict = []

        self.hostprDict = ['1fichier.com', 'oboom.com', 'rapidgator.net', 'rg.to', 'uploaded.net', 'uploaded.to', 'ul.to', 'filefactory.com', 'nitroflare.com', 'turbobit.net', 'uploadrocket.net']

        self.hostpairDict = ['flashx.tv', 'flashx.to', 'flashx.sx', 'flashx.bz', 'flashx.cc', 'hugefiles.net', 'kingfiles.net', 'openload.io', 'openload.co', 'oload.tv', 'oload.stream', 'oload.win', 'oload.download', 'oload.info', 'oload.icu', 'oload.fu', 'openload.pw', 'thevideo.me', 'vidup.me', 'streamin.to', 'torba.se']

        self.hosthqDict = ['bitporno.com', 'cloudvideo.tv', 'filez.tv', 'fruitadblock.net', 'fruitstreams.com', 'google.com', 'gvideo', 'oload.download', 'oload.stream', 'oload.tv', 'oload.tv', 'oload.win', 'openload.co', 'openload.io', 'rapidvideo.com', 'rapidvideo.ws', 'raptu.com', 'streamango.com', 'streamcherry.com', 'thevideo.me', 'uptobox.com', 'uptostream.com', 'vidoza.net', 'vivo.sx']

        self.HosterBlockingList = control.setting('hosts.blocking')
        if self.HosterBlockingList == "true":
            self.HosterBlockingList1 = control.setting('HosterBlockingList1')
            self.HosterBlockingList2 = control.setting('HosterBlockingList2')
            self.HosterBlockingList3 = control.setting('HosterBlockingList3')
            self.HosterBlockingList4 = control.setting('HosterBlockingList4')
            self.HosterBlockingList5 = control.setting('HosterBlockingList5')
            self.HosterBlockingList6 = control.setting('HosterBlockingList6')
            self.HosterBlockingList7 = control.setting('HosterBlockingList7')
            self.HosterBlockingList8 = control.setting('HosterBlockingList8')
            self.HosterBlockingList9 = control.setting('HosterBlockingList9')
            self.HosterBlockingList10 = control.setting('HosterBlockingList10')

            self.hostblockingDict = [self.HosterBlockingList1, self.HosterBlockingList2, self.HosterBlockingList3, self.HosterBlockingList4, self.HosterBlockingList5, self.HosterBlockingList6, self.HosterBlockingList7, self.HosterBlockingList8, self.HosterBlockingList9, self.HosterBlockingList10]
        else:
            pass

        self.hostblockDict = [] #Altbestand. Wofür?

    def getPremColor(self, n):
        if n == '0': n = 'blue'
        elif n == '1': n = 'red'
        elif n == '2': n = 'yellow'
        elif n == '3': n = 'deeppink'
        elif n == '4': n = 'cyan'
        elif n == '5': n = 'lawngreen'
        elif n == '6': n = 'gold'
        elif n == '7': n = 'magenta'
        elif n == '8': n = 'yellowgreen'
        elif n == '9': n = 'nocolor'
        else: n == 'blue'
        return n
