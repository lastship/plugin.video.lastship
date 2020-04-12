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

import os, base64, sys, urllib2
import xbmc, xbmcaddon, xbmcgui
from resources.lib.modules import control
from resources.lib.modules import trakt
from resources.lib.modules import cache

sysaddon = sys.argv[0];
syshandle = int(sys.argv[1]);
control.moderator()

artPath = control.artPath();
addonFanart = control.addonFanart()

imdbCredentials = False if control.setting('imdb.user') == '' else True

traktCredentials = trakt.getTraktCredentialsInfo()

traktIndicators = trakt.getTraktIndicatorsInfo()

queueMenu = "Eintrag zur Warteschlange hinzufügen"


class navigator:
    ADDON_ID = xbmcaddon.Addon().getAddonInfo('id')
    HOMEPATH = xbmc.translatePath('special://home/')
    ADDONSPATH = os.path.join(HOMEPATH, 'addons')
    THISADDONPATH = os.path.join(ADDONSPATH, ADDON_ID)
    NEWSFILE = base64.b64decode('aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2xhc3RzaGlwL3BsdWdpbi52aWRlby5sYXN0c2hpcC9uaWdodGx5L3doYXRzbmV3LnR4dA==')
    LOCALNEWS = os.path.join(THISADDONPATH, 'whatsnew.txt')

    def root(self):
        
        self.addDirectoryItem('[COLOR=lime]Infos und Updates[/COLOR]', 'newsNavigator', 'news_paper.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("Suche", 'searchNavigator', 'search.png', 'DefaultFolder.png', isFolder=not self.quickSearchActivated())
        self.addDirectoryItem("Filme", 'movieNavigator', 'movies.png', 'DefaultMovies.png')
        self.addDirectoryItem("TV-Serien", 'tvNavigator', 'tvshows.png', 'DefaultTVShows.png')

        if not control.setting('lists.widget') == '0':
            self.addDirectoryItem("Meine Filme", 'mymovieNavigator', 'mymovies.png', 'DefaultVideoPlaylists.png')
            self.addDirectoryItem("Meine TV-Serien", 'mytvNavigator', 'mytvshows.png', 'DefaultVideoPlaylists.png')

        if not control.setting('movie.widget') == '0':
            self.addDirectoryItem("Neue Filme", 'movieWidget', 'latest-movies.png', 'DefaultRecentlyAddedMovies.png')

        if (traktIndicators == True and not control.setting('tv.widget.alt') == '0') or (
                traktIndicators == False and not control.setting('tv.widget') == '0'):
            self.addDirectoryItem("Neue Episoden", 'tvWidget', 'latest-episodes.png', 'DefaultRecentlyAddedEpisodes.png')

        self.addDirectoryItem("Werkzeuge", 'toolNavigator', 'tools.png', 'DefaultAddonProgram.png')

        downloads = True if control.setting('downloads') == 'true' and (
                len(control.listDir(control.setting('movie.download.path'))[0]) > 0 or len(
            control.listDir(control.setting('tv.download.path'))[0]) > 0) else False
        if downloads == True:
            self.addDirectoryItem("Downloads", 'downloadNavigator', 'downloads.png', 'DefaultFolder.png')

        if control.setting('DevUpdate') == 'true':
            self.addDirectoryItem("Nightly Updates", 'devUpdateNavigator', 'nightly_update.png', 'DefaultAddonProgram.png')

        self.endDirectory()

    #######################################################################
    # News and Update Code
    def news(self):
        AddonVersion = control.addon('plugin.video.lastship').getAddonInfo('version')
        r = open(self.LOCALNEWS)
        compfile = r.read()
        self.showText('[B][COLOR springgreen]Infos und Updates[/COLOR][/B]' + ' ' + '---' + ' ' + '(Version: ' + AddonVersion + ')', compfile)

    def showText(self, heading, text):
        id = 10147
        xbmc.executebuiltin('ActivateWindow(%d)' % id)
        xbmc.sleep(500)
        win = xbmcgui.Window(id)
        retry = 50
        while (retry > 0):
            try:
                xbmc.sleep(10)
                retry -= 1
                win.getControl(1).setLabel(heading)
                win.getControl(5).setText(text)
                quit()
                return
            except:
                pass

    #######################################################################

    def movies(self, lite=False):
        self.addDirectoryItem("Genres", 'movieGenres', 'genres.png', 'DefaultMovies.png')
        self.addDirectoryItem("FSK", 'movieCertificates', 'certificates.png', 'DefaultMovies.png')
        self.addDirectoryItem("Neue Filme", 'movieWidget', 'latest-movies.png', 'DefaultRecentlyAddedMovies.png')
        self.addDirectoryItem("In den Kinos", 'movies&url=theaters', 'in-theaters.png', 'DefaultRecentlyAddedMovies.png')
        self.addDirectoryItem("Bald verfügbar", 'movies&url=anticipated', 'movies.png', 'DefaultMovies.png')
        self.addDirectoryItem("Auszeichnungen & Co", 'movieAwards', 'auszeichnungen.png', 'DefaultMovies.png')
        self.addDirectoryItem("Studios", 'movieStudios', 'movies.png', 'DefaultMovies.png')
        self.addDirectoryItem("Jahr", 'movieYears', 'years.png', 'DefaultMovies.png')
        self.addDirectoryItem("Herkunftsland", 'movieCountryOfOrigin', 'languages.png', 'DefaultMovies.png')
        if control.setting('PersonalMovieList') == 'true':
            self.addDirectoryItem("IMDB-Listen", 'moviePersonalList', 'imdb.png', 'DefaultMovies.png')
        else:
            pass
        self.addDirectoryItem("Personen", 'moviePersons', 'people.png', 'DefaultMovies.png')

        if lite == False:
            if not control.setting('lists.widget') == '0':
                self.addDirectoryItem("Meine Filme", 'mymovieliteNavigator', 'mymovies.png', 'DefaultVideoPlaylists.png')

            self.addDirectoryItem("Suche nach Darstellern/Crew", 'moviePerson', 'people-search.png', 'DefaultMovies.png', isFolder=False)
            self.addDirectoryItem("Suche", 'movieSearch', 'search.png', 'DefaultMovies.png')

        self.endDirectory()

    def mymovies(self, lite=False):
        self.accountCheck()

        if traktCredentials == True and imdbCredentials == True:
            self.addDirectoryItem("[B]Trakt[/B]-Sammlung", 'movies&url=traktcollection', 'trakt.png', 'DefaultMovies.png', queue=True,
                                  context=("Zur Bibliothek hinzufügen", 'moviesToLibrary&url=traktcollection'))
            self.addDirectoryItem("[B]Trakt[/B]-Merkliste", 'movies&url=traktwatchlist', 'trakt.png', 'DefaultMovies.png', queue=True,
                                  context=("Zur Bibliothek hinzufügen", 'moviesToLibrary&url=traktwatchlist'))
            self.addDirectoryItem("[B]IMDb[/B]-Merkliste", 'movies&url=imdbwatchlist', 'imdb.png', 'DefaultMovies.png', queue=True)

        elif traktCredentials == True:
            self.addDirectoryItem("[B]Trakt[/B]-Sammlung", 'movies&url=traktcollection', 'trakt.png', 'DefaultMovies.png', queue=True,
                                  context=("Zur Bibliothek hinzufügen", 'moviesToLibrary&url=traktcollection'))
            self.addDirectoryItem("[B]Trakt[/B]-Merkliste", 'movies&url=traktwatchlist', 'trakt.png', 'DefaultMovies.png', queue=True,
                                  context=("Zur Bibliothek hinzufügen", 'moviesToLibrary&url=traktwatchlist'))

        elif imdbCredentials == True:
            self.addDirectoryItem("[B]IMDb[/B]-Merkliste", 'movies&url=imdbwatchlist', 'imdb.png', 'DefaultMovies.png', queue=True)
            self.addDirectoryItem("[B]IMDb[/B]-Merkliste", 'movies&url=imdbwatchlist2', 'imdb.png', 'DefaultMovies.png', queue=True)

        if traktCredentials == True:
            self.addDirectoryItem("Empfohlen", 'movies&url=traktfeatured', 'trakt.png', 'DefaultMovies.png', queue=True)

        elif imdbCredentials == True:
            self.addDirectoryItem("Empfohlen", 'movies&url=featured', 'imdb.png', 'DefaultMovies.png', queue=True)

        if traktIndicators == True:
            self.addDirectoryItem("Verlauf", 'movies&url=trakthistory', 'trakt.png', 'DefaultMovies.png', queue=True)

        self.addDirectoryItem("Film-Listen", 'movieUserlists', 'userlists.png', 'DefaultMovies.png')

        if lite == False:
            self.addDirectoryItem("Entdecken", 'movieliteNavigator', 'movies.png', 'DefaultMovies.png')
            self.addDirectoryItem("Suche nach Darstellern/Crew", 'moviePerson', 'people-search.png', 'DefaultMovies.png')
            self.addDirectoryItem("Suche", 'movieSearch', 'search.png', 'DefaultMovies.png')

        self.endDirectory()

    def tvshows(self, lite=False):
        self.addDirectoryItem("Genres", 'tvGenres', 'genres.png', 'DefaultTVShows.png')
        self.addDirectoryItem("FSK", 'tvCertificates', 'certificates.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Neue TV-Serien", 'tvshows&url=premiere', 'new-tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Neue Episoden", 'calendar&url=added', 'latest-episodes.png', 'DefaultRecentlyAddedEpisodes.png', queue=True)
        self.addDirectoryItem("Bald verfügbar", 'tvshows&url=anticipated', 'new-tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem("TV-Sender", 'tvNetworks', 'networks.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Auszeichnungen & Co", 'tvAwards', 'auszeichnungen.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Herkunftsland", 'tvCountryOfOrigin', 'languages.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Heute auf Sendung", 'tvshows&url=airing', 'airing-today.png', 'DefaultTVShows.png')
        self.addDirectoryItem("TV-Kalender", 'calendars', 'calendar.png', 'DefaultRecentlyAddedEpisodes.png')

        if lite == False:
            if not control.setting('lists.widget') == '0':
                self.addDirectoryItem("Meine TV-Serien", 'mytvliteNavigator', 'mytvshows.png', 'DefaultVideoPlaylists.png')

            self.addDirectoryItem("Suche nach Darstellern/Crew", 'tvPerson', 'people-search.png', 'DefaultTVShows.png')
            self.addDirectoryItem("Suche", 'tvSearch', 'search.png', 'DefaultTVShows.png')

        self.endDirectory()

    def mytvshows(self, lite=False):
        self.accountCheck()

        if traktCredentials == True:
            self.addDirectoryItem("Angefangene/nicht beendete Episoden", 'calendar&url=onDeck', 'trakt.png', 'DefaultTVShows.png')
            self.addDirectoryItem("[B]Trakt[/B]-Sammlung", 'tvshows&url=traktcollection', 'trakt.png', 'DefaultTVShows.png', context=("Zur Bibliothek hinzufügen", 'tvshowsToLibrary&url=traktcollection'))
            self.addDirectoryItem("[B]Trakt[/B]-Merkliste", 'tvshows&url=traktwatchlist', 'trakt.png', 'DefaultTVShows.png', context=("Zur Bibliothek hinzufügen", 'tvshowsToLibrary&url=traktwatchlist'))

            if imdbCredentials == True:
                self.addDirectoryItem("[B]IMDb[/B]-Merkliste", 'tvshows&url=imdbwatchlist', 'imdb.png', 'DefaultTVShows.png')

        if traktCredentials == False and imdbCredentials == True:
            self.addDirectoryItem("[B]IMDb[/B]-Merkliste", 'tvshows&url=imdbwatchlist', 'imdb.png', 'DefaultTVShows.png')
            self.addDirectoryItem("[B]IMDb[/B]-Merkliste", 'tvshows&url=imdbwatchlist2', 'imdb.png', 'DefaultTVShows.png')
      
        if traktCredentials == True:
            self.addDirectoryItem("Empfohlen", 'tvshows&url=traktfeatured', 'trakt.png', 'DefaultTVShows.png')
        elif imdbCredentials == True:
            self.addDirectoryItem("Empfohlen", 'tvshows&url=trending', 'imdb.png', 'DefaultMovies.png', queue=True)

        if traktIndicators == True:
            self.addDirectoryItem("Verlauf", 'calendar&url=trakthistory', 'trakt.png', 'DefaultTVShows.png', queue=True)
            self.addDirectoryItem("Fortschritt", 'calendar&url=progress', 'trakt.png', 'DefaultRecentlyAddedEpisodes.png', queue=True)
            self.addDirectoryItem("Meine neuesten Episoden", 'calendar&url=mycalendar', 'trakt.png', 'DefaultRecentlyAddedEpisodes.png', queue=True)

        self.addDirectoryItem("TV-Serien-Listen", 'tvUserlists', 'userlists.png', 'DefaultTVShows.png')

        if traktCredentials == True:
            self.addDirectoryItem("Episoden-Listen", 'episodeUserlists', 'userlists.png', 'DefaultTVShows.png')

        if lite == False:
            self.addDirectoryItem("Entdecken", 'tvliteNavigator', 'tvshows.png', 'DefaultTVShows.png')
            self.addDirectoryItem("Suche nach Darstellern/Crew", 'tvPerson', 'people-search.png', 'DefaultTVShows.png')
            self.addDirectoryItem("Suche", 'tvSearch', 'search.png', 'DefaultTVShows.png')

        self.endDirectory()

    def tools(self):
        self.addDirectoryItem("[B]EINSTELLUNGEN[/B]", 'openSettings', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Bibliothek", 'libraryNavigator', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Anzeige-Typen", 'viewsNavigator', 'tools.png', 'DefaultAddonProgram.png')
        if control.setting('FaultLogger.enabled') == 'true':
            self.addDirectoryItem("[B]LASTSHIP[/B]: Fehlerhafte Provider anzeigen", 'showFaultyProvider', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Suchverlauf leeren", 'clearCacheSearch', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Cache leeren", 'clearCache', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Indexseiten-Cache leeren", 'clearSources', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Metadaten-Cache leeren", 'clearCacheMeta', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Alle Caches leeren", 'clearCacheAll', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]Trakt[/B]: Berechtigung", 'authTrakt', 'trakt.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("URL-Resolver Einstellungen", 'urlResolver', 'urlresolver.png', 'DefaultAddonProgram.png')

        self.endDirectory()

    def library(self):
        self.addDirectoryItem("[B]LASTSHIP[/B]: Bibliothek aktualisieren", 'updateLibrary&query=tool', 'library_update.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem("[B]LASTSHIP[/B]: Film-Ordner", control.setting('library.movie'), 'movies.png', 'DefaultMovies.png',
                              isAction=False)
        self.addDirectoryItem("[B]LASTSHIP[/B]: TV-Serien-Ordner", control.setting('library.tv'), 'tvshows.png', 'DefaultTVShows.png', isAction=False)

        if trakt.getTraktCredentialsInfo():
            self.addDirectoryItem("[B]TRAKT[/B]: Film-Sammlung importieren", 'moviesToLibrary&url=traktcollection', 'trakt.png', 'DefaultMovies.png')
            self.addDirectoryItem("[B]TRAKT[/B]: Film-Merkliste importieren", 'moviesToLibrary&url=traktwatchlist', 'trakt.png', 'DefaultMovies.png')
            self.addDirectoryItem("[B]TRAKT[/B]: TV-Serien-Sammlung importieren", 'tvshowsToLibrary&url=traktcollection', 'trakt.png', 'DefaultTVShows.png')
            self.addDirectoryItem("[B]TRAKT[/B]: TV-Serien-Merkliste importieren", 'tvshowsToLibrary&url=traktwatchlist', 'trakt.png', 'DefaultTVShows.png')

        self.endDirectory()

    def downloads(self):
        movie_downloads = control.setting('movie.download.path')
        tv_downloads = control.setting('tv.download.path')

        if len(control.listDir(movie_downloads)[0]) > 0:
            self.addDirectoryItem("Filme", movie_downloads, 'movies.png', 'DefaultMovies.png', isAction=False)
        if len(control.listDir(tv_downloads)[0]) > 0:
            self.addDirectoryItem("TV-Serien", tv_downloads, 'tvshows.png', 'DefaultTVShows.png', isAction=False)

        self.endDirectory()

    def search(self):
        self.addDirectoryItem("Filme", 'movieSearch', 'search.png', 'DefaultMovies.png')
        self.addDirectoryItem("TV-Serien", 'tvSearch', 'search.png', 'DefaultTVShows.png')
        self.addDirectoryItem("Darsteller/Crew (Filme)", 'moviePerson', 'people-search.png', 'DefaultMovies.png', isFolder=False)
        self.addDirectoryItem("Darsteller/Crew (TV-Serien)", 'tvPerson', 'people-search.png', 'DefaultTVShows.png', isFolder=False)

        self.endDirectory()

    def views(self):
        try:
            control.idle()

            items = [("Filme", 'movies'), ("TV-Serien", 'tvshows'),
                     ("Staffeln", 'seasons'),
                     ("Episoden", 'episodes')]

            select = control.selectDialog([i[0] for i in items], "[B]LASTSHIP[/B]: Anzeige-Typen")

            if select == -1: return

            content = items[select][1]

            title = "HIER KLICKEN, UM ANSICHT ZU SPEICHERN"
            url = '%s?action=addView&content=%s' % (sys.argv[0], content)

            poster, banner, fanart = control.addonPoster(), control.addonBanner(), control.addonFanart()

            item = control.item(label=title)
            item.setInfo(type='Video', infoLabels={'title': title})
            item.setArt({'icon': poster, 'thumb': poster, 'poster': poster, 'banner': banner})
            item.setProperty('Fanart_Image', fanart)

            control.addItem(handle=int(sys.argv[1]), url=url, listitem=item, isFolder=False)
            control.content(int(sys.argv[1]), content)
            control.directory(int(sys.argv[1]), cacheToDisc=True)

            from resources.lib.modules import views
            views.setView(content, {})
        except:
            return

    def accountCheck(self):
        if traktCredentials == False and imdbCredentials == False:
            control.idle()
            control.infoDialog("Kein Trakt- oder IMDb-Konto gefunden", sound=True, icon='WARNING')
            sys.exit()

    def infoCheck(self, version):
        try:
            control.infoDialog('lastship.ch/forum/', "HILFE", time=5000,
                               sound=False)
            return '1'
        except:
            return '1'

    def clearCache(self):
        control.idle()
        yes = control.yesnoDialog("Sind Sie sicher?", '', '')
        if not yes: return
        cache.cache_clear()
        control.infoDialog("Vorgang abgeschlossen", sound=True, icon='INFO')

    def clearCacheMeta(self):
        control.idle()
        yes = control.yesnoDialog("Sind Sie sicher?", '', '')
        if not yes: return
        cache.cache_clear_meta()
        control.infoDialog("Vorgang abgeschlossen", sound=True, icon='INFO')

    def clearCacheProviders(self):
        control.idle()
        yes = control.yesnoDialog("Sind Sie sicher?", '', '')
        if not yes: return
        cache.cache_clear_providers()
        control.infoDialog("Vorgang abgeschlossen", sound=True, icon='INFO')

    def clearCacheSearch(self):
        control.idle()
        yes = control.yesnoDialog("Sind Sie sicher?", '', '')
        if not yes: return
        cache.cache_clear_search()
        control.infoDialog("Vorgang abgeschlossen", sound=True, icon='INFO')

    def clearCacheAll(self):
        control.idle()
        yes = control.yesnoDialog("Sind Sie sicher?", '', '')
        if not yes: return
        cache.cache_clear_all()
        from resources.lib.modules.handler.requestHandler import cRequestHandler
        cRequestHandler('dummy').clearCache()
        control.infoDialog("Vorgang abgeschlossen", sound=True, icon='INFO')

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        thumb = os.path.join(artPath, thumb) if not artPath == None else icon
        cm = []
        if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
        if not context == None: cm.append(
            (context[0], 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        item = control.item(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb})
        if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)
        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self):
        control.content(syshandle, 'addons')
        control.directory(syshandle, cacheToDisc=True)

    def quickSearchActivated(self):
        return control.setting('search.quick') == '1'
