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


from resources.lib.modules import trakt
from resources.lib.modules import cleangenre
from resources.lib.modules import control
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import playcount
from resources.lib.modules import workers
from resources.lib.modules import views
from resources.lib.modules import utils
from resources.lib.indexers import navigator
from resources.lib.modules import log_utils
from datetime import date, timedelta

import os,sys,re,json,urllib,urlparse,datetime

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?',''))) if len(sys.argv) > 1 else dict()

action = params.get('action')

control.moderator()


class movies:
    def __init__(self):
        self.list = []

        self.imdb_link = 'http://www.imdb.com'
        self.trakt_link = 'http://api.trakt.tv'
        self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
        self.systime = (self.datetime).strftime('%Y%m%d%H%M%S%f')
        self.year_date = (self.datetime - datetime.timedelta(days = 365)).strftime('%Y-%m-%d')
        self.today_date = (self.datetime).strftime('%Y-%m-%d')
        self.trakt_user = control.setting('trakt.user').strip()
        self.imdb_user = control.setting('imdb.user').replace('ur', '')
        self.tm_user = control.setting('tm.user')
        self.fanart_tv_user = control.setting('fanart.tv.user')
        self.user = str(control.setting('fanart.tv.user')) + str(control.setting('tm.user'))
        self.lang = control.apiLanguage()['trakt']
        self.hidecinema = control.setting('hidecinema')
        self.filterbyyear = control.setting('filter.movies.byyear')

        self.search_link = 'http://api.trakt.tv/search/movie?limit=20&page=1&query='
        self.fanart_tv_art_link = 'http://webservice.fanart.tv/v3/movies/%s'
        self.fanart_tv_level_link = 'http://webservice.fanart.tv/v3/level'
        self.tm_art_link = 'http://api.themoviedb.org/3/movie/%s/images?api_key=%s&language=en-US&include_image_language=en,%s,null' % ('%s', self.tm_user, self.lang)
        self.tm_img_link = 'http://image.tmdb.org/t/p/w%s%s'
        
        self.clear_link = '%s'
        self.persons_link = 'http://www.imdb.com/search/name?count=100&name='
        self.personlist_link = 'http://www.imdb.com/search/name?count=100&gender=male,female'
        self.person_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&production_status=released&role=%s'
        self.keyword_link = 'http://www.imdb.com/search/title?keywords=%s&title_type=feature,tv_movie,documentary&adult=include'
        self.award_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&groups=%s&adult=include'
        self.countryoforigin_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&country_of_origin=%s&adult=include'
        self.studio_link ='http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&companies=%s&adult=include'
        self.personallist_link = 'http://www.imdb.com/list/%s'
        self.theaters_link = 'http://www.imdb.com/search/title?release_date=date[365],date[0]&num_votes=1000,&groups=now-playing-us&adult=include'
        self.year_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&production_status=released&year=%s,%s&adult=include&start=%s'
        self.boxoffice_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&production_status=released&sort=boxoffice_gross_us,desc'

        if self.hidecinema == 'true':
                delay = (date.today() - timedelta(90))
                start_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&release_date=,%s' % (delay)
                self.popular_link = start_link + '&num_votes=1000,&production_status=released&groups=top_1000&adult=include'
                self.views_link =  start_link + '&num_votes=1000,&production_status=released&sort=num_votes,desc&adult=include'
                self.featured_link = start_link + '&production_status=released&adult=include'
                self.countryoforigin_link = '&production_status=released&country_of_origin=%s&adult=include'
                self.genre_link = start_link + '&producion_status=released&genres=%s&adult=include'
                self.studio_link = start_link + '&companies=%s&adult=include'
                self.certification_link = start_link + '&certificates=DE:%s&adult=include'
                self.boxoffice_link = start_link + '&production_status=released&sort=boxoffice_gross_us&adult=include'
        else:
            self.popular_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&num_votes=1000,&groups=top_1000&adult=include'
            self.views_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&num_votes=1000,&sort=num_votes,desc&adult=include'
            self.featured_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&num_votes=1000,&production_status=released&release_date=date[365],date[60]&adult=include'
            self.genre_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&num_votes=100,&release_date=,date[0]&genres=%s&adult=include'
            self.certification_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&certificates=DE:%s&adult=include'

        if self.filterbyyear == 'true':
            from_year = control.setting('movies.byyear.from')
            to_year = control.setting('movies.byyear.to')
            self.views_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&year=%s,%s&num_votes=1000,&production_status=released&sort=num_votes,desc&adult=include' % (str(from_year), str(to_year))
            self.genre_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&num_votes=100,&genres=%s&year=%s,%s&adult=include' % ('%s', str(from_year), str(to_year))
            self.award_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&groups=%s&year=%s,%s&adult=include' % ('%s', str(from_year), str(to_year))
            self.countryoforigin_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&country_of_origin=%s&year=%s,%s&adult=include' % ('%s', str(from_year), str(to_year))
            self.boxoffice_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&production_status=released&sort=boxoffice_gross_us,desc&year=%s,%s&adult=include' % (str(from_year), str(to_year))
            self.popular_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&num_votes=1000,&production_status=released&groups=top_1000&year=%s,%s&adult=include' % (str(from_year), str(to_year))
            self.genre_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary,documentary&num_votes=100,&release_date=,date[0]&genres=%s&year=%s,%s&adult=include' % ('%s', str(from_year), str(to_year))
            self.studio_link ='http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&companies=%s&year=%s,%s&adult=include' % ('%s', str(from_year), str(to_year))
            self.certification_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie,documentary&certificates=DE:%s&year=%s,%s&adult=include' % ('%s', str(from_year), str(to_year))
            self.keyword_link = 'http://www.imdb.com/search/title?keywords=%s&title_type=feature,tv_movie,documentary&year=%s,%s&adult=include' % ('%s', str(from_year), str(to_year))


        self.added_link  = 'http://www.imdb.com/search/title?title_type=feature,tv_movie&languages=en&num_votes=500,&production_status=released&release_date=%s,%s&sort=release_date,desc&count=20&start=1' % (self.year_date, self.today_date)
        self.trending_link = 'http://api.trakt.tv/movies/trending?limit=40&page=1'
        self.anticipated_link = 'http://api.trakt.tv/movies/anticipated?limit=100?page=1'
        self.traktlists_link = 'http://api.trakt.tv/users/me/lists'
        self.traktlikedlists_link = 'http://api.trakt.tv/users/likes/lists?limit=1000000'
        self.traktlist_link = 'http://api.trakt.tv/users/%s/lists/%s/items'
        self.traktcollection_link = 'http://api.trakt.tv/users/me/collection/movies'
        self.traktwatchlist_link = 'http://api.trakt.tv/users/me/watchlist/movies'
        self.traktfeatured_link = 'http://api.trakt.tv/recommendations/movies?limit=40'
        self.trakthistory_link = 'http://api.trakt.tv/users/me/history/movies?limit=40&page=1'
        self.imdblists_link = 'http://www.imdb.com/user/ur%s/lists?tab=all&sort=mdfd&order=desc&filter=titles' % self.imdb_user
        self.imdblist_link = 'http://www.imdb.com/list/%s/?view=detail&sort=alpha,asc&title_type=movie,short,tvMovie,tvSpecial,video&start=1'
        self.imdblist2_link = 'http://www.imdb.com/list/%s/?view=detail&sort=date_added,desc&title_type=movie,short,tvMovie,tvSpecial,video&start=1'
        self.imdbwatchlist_link = 'http://www.imdb.com/user/ur%s/watchlist?sort=alpha,asc' % self.imdb_user
        self.imdbwatchlist2_link = 'http://www.imdb.com/user/ur%s/watchlist?sort=date_added,desc' % self.imdb_user


    def get(self, url, idx=True, create_directory=True):
        try:
            try: url = getattr(self, url + '_link')
            except: pass

            try: u = urlparse.urlparse(url).netloc.lower()
            except: pass


            if u in self.trakt_link and '/users/' in url:
                try:
                    if url == self.trakthistory_link: raise Exception()
                    if not '/users/me/' in url: raise Exception()
                    if trakt.getActivity() > cache.timeout(self.trakt_list, url, self.trakt_user): raise Exception()
                    self.list = cache.get(self.trakt_list, 720, url, self.trakt_user)
                except:
                    self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)

                if '/users/me/' in url and '/collection/' in url:
                    self.list = sorted(self.list, key=lambda k: utils.title_key(k['title']))

                if idx == True: self.worker()

            elif u in self.trakt_link and self.search_link in url:
                self.list = cache.get(self.trakt_list, 1, url, self.trakt_user)
                if idx == True: self.worker(level=0)

            elif u in self.trakt_link:
                self.list = cache.get(self.trakt_list, 24, url, self.trakt_user)
                if idx == True: self.worker()


            elif u in self.imdb_link and ('/user/' in url or '/list/' in url):
                self.list = cache.get(self.imdb_list, 0, url)
                if idx == True: self.worker()

            elif u in self.imdb_link:
                self.list = cache.get(self.imdb_list, 24, url)
                if idx == True: self.worker()


            if self.list == None or len(self.list) == 0:
                control.idle()
                control.infoDialog("Nichts gefunden", time=8000)
            elif idx == True and create_directory == True:
                    self.movieDirectory(self.list)
            return self.list
        except:
            pass


    def widget(self):
        setting = control.setting('movie.widget')

        if setting == '2':
            self.get(self.trending_link)
        elif setting == '3':
            self.get(self.popular_link)
        elif setting == '4':
            self.get(self.theaters_link)
        elif setting == '5':
            self.get(self.added_link)
        else:
            self.get(self.featured_link)

    def search(self):

        navigator.navigator().addDirectoryItem("Neue Suche", 'movieSearchnew', 'search.png', 'DefaultMovies.png', isFolder=False)
        try: from sqlite3 import dbapi2 as database
        except: from pysqlite2 import dbapi2 as database

        dbcon = database.connect(control.searchFile)
        dbcur = dbcon.cursor()

        try:
            dbcur.executescript("CREATE TABLE IF NOT EXISTS movies (ID Integer PRIMARY KEY AUTOINCREMENT, term);")
        except:
            pass

        dbcur.execute("SELECT * FROM movies ORDER BY ID DESC")
        lst = []

        delete_option = False
        for (id,term) in dbcur.fetchall():
            if term not in str(lst):
                delete_option = True
                navigator.navigator().addDirectoryItem(term, 'movieSearchterm&name=%s' % term, 'search.png', 'DefaultMovies.png', isFolder=False)
                lst += [(term)]
        dbcur.close()

        if delete_option:
            navigator.navigator().addDirectoryItem("Suchverlauf löschen", 'clearCacheSearch', 'tools.png', 'DefaultAddonProgram.png')

        navigator.navigator().endDirectory()

    def search_new(self):
            control.idle()

            t = "Suche"
            k = control.keyboard('', t) ; k.doModal()
            q = k.getText() if k.isConfirmed() else None

            if (q == None or q == ''): return

            try: from sqlite3 import dbapi2 as database
            except: from pysqlite2 import dbapi2 as database

            dbcon = database.connect(control.searchFile)
            dbcur = dbcon.cursor()
            dbcur.execute("INSERT INTO movies VALUES (?,?)", (None,q.decode('utf-8')))
            dbcon.commit()
            dbcur.close()
            url = self.search_link + urllib.quote_plus(q)
            url = '%s?action=moviePage&url=%s' % (sys.argv[0], urllib.quote_plus(url))
            control.execute('Container.Update(%s)' % url)

    def search_term(self, name):
            control.idle()

            url = self.search_link + urllib.quote_plus(name)
            url = '%s?action=moviePage&url=%s' % (sys.argv[0], urllib.quote_plus(url))
            control.execute('Container.Update(%s)' % url)

    def person(self):
        try:
            control.idle()

            t = "Suche"
            k = control.keyboard('', t) ; k.doModal()
            q = k.getText() if k.isConfirmed() else None

            if (q == None or q == ''): return

            url = self.persons_link + urllib.quote_plus(q)
            url = '%s?action=moviePersons&url=%s' % (sys.argv[0], urllib.quote_plus(url))
            control.execute('Container.Update(%s)' % url)
        except:
            return

    def genres(self):

        genre = [
            ('Adventure', 'adventure', True),
            ('Action', 'action', True),
            ('Animation', 'animation', True),
            ('Anime', 'anime', False),
            ('Biography', 'biography', True),
            ('Documentary', 'documentary', True),
            ('Drama', 'drama', True),
            ('Family', 'family', True),
            ('Fantasy', 'fantasy', True),
            ('History', 'history', True),
            ('Horror', 'horror', True),
            ('Comedy', 'comedy', True),
            ('War', 'war', True),
            ('Crime', 'crime', True),
            ('Romance', 'romance', True),
            ('Musical', 'musical', True),
            ('Music', 'music', True),
            ('Mystery', 'mystery', True),
            ('Science Fiction', 'sci_fi', True),
            ('Sport', 'sport', True),
            ('Superhelden', 'superhero', False),
            ('Thriller', 'thriller', True),
            ('Western', 'western', True)
        ]

        self.PersonalMovieGenre = control.setting('PersonalMovieGenre')
        if self.PersonalMovieGenre == "true":
            genre.append((control.setting('PersonalMovieGenreTitle1'),control.setting('PersonalMovieGenre1'),False))
            genre.append((control.setting('PersonalMovieGenreTitle2'),control.setting('PersonalMovieGenre2'),False))
            genre.append((control.setting('PersonalMovieGenreTitle3'),control.setting('PersonalMovieGenre3'),False))
            genre.append((control.setting('PersonalMovieGenreTitle4'),control.setting('PersonalMovieGenre4'),False))
            genre.append((control.setting('PersonalMovieGenreTitle5'),control.setting('PersonalMovieGenre5'),False))


        for i in genre: self.list.append(
        {
            'name': cleangenre.lang(i[0], self.lang),
            'url': self.genre_link % i[1] if i[2] else self.keyword_link % i[1],
            'image': 'genres.png',
            'action': 'movies'
        })

        self.addDirectory(self.list)
        return self.list

    def personallist(self):
        self.PersonalMovieList = control.setting('PersonalMovieList')
        if self.PersonalMovieList == "true":
            self.PersonalMovieList1 = control.setting('PersonalMovieList1')
            self.PersonalMovieList2 = control.setting('PersonalMovieList2')
            self.PersonalMovieList3 = control.setting('PersonalMovieList3')
            self.PersonalMovieList4 = control.setting('PersonalMovieList4')
            self.PersonalMovieList5 = control.setting('PersonalMovieList5')
            self.PersonalMovieListTitle1 = control.setting('PersonalMovieListTitle1')
            self.PersonalMovieListTitle2 = control.setting('PersonalMovieListTitle2')
            self.PersonalMovieListTitle3 = control.setting('PersonalMovieListTitle3')
            self.PersonalMovieListTitle4 = control.setting('PersonalMovieListTitle4')
            self.PersonalMovieListTitle5 = control.setting('PersonalMovieListTitle5')

            personallists = [
            (self.PersonalMovieListTitle1, self.PersonalMovieList1),
            (self.PersonalMovieListTitle2, self.PersonalMovieList2),
            (self.PersonalMovieListTitle3, self.PersonalMovieList3),
            (self.PersonalMovieListTitle4, self.PersonalMovieList4),
            (self.PersonalMovieListTitle5, self.PersonalMovieList5)
            ]

        for i in personallists: self.list.append(
        {
            'name': str(i[0]),
            'url': self.personallist_link % i[1],
            'image': 'imdb.png',
            'action': 'movies'
        })

        self.addDirectory(self.list)
        return self.list
        
    def award(self):
            awards = [
#             Folgende 2 Punkte werden nicht gefiltert!
            ('Meistbewertet', self.views_link, False, 'most-voted.png'),
            ('Aktive Betrachter', self.trending_link, False, 'people-watching.png'),
            ('Bestes Einspielergebnis', self.boxoffice_link, False, 'box-office.png'),
            ('Oskar-Gewinner: Bester Film', 'best_picture_winner', True, 'oscar-winners.png'),
            ('Oskar-Gewinner: Bester Regisseur', 'best_director_winner', True, 'oscar-winners.png'),
            ('Oskar-Gewinner', 'oscar_winner', True, 'oscar-winners.png'),
            ('Oskar-Nominierung', 'oscar_nominee', True, 'oscar-winners.png'),
            ('Emmy-Gewinner', 'emmy_winner', True, 'emmy.png'),
            ('Emmy-Nominierung', 'emmy_nominee', True, 'emmy.png'),
            ('Golden-Globe: Gewinner', 'golden_globe_winner', True, 'globe.png'),
            ('Golden-Globe: Nominierung', 'golden_globe_nominee', True, 'globe.png'),
            ('Goldene-Himbeere: Gewinner', 'razzie_winner', True, 'beere.png'),
            ('Goldene-Himbeere: Nominierung', 'razzie_nominee', True, 'beere.png'),
            ('IMDB Top 250', 'top_250', True, 'featured.png'),
            ('IMDB Top 1000', 'top_1000', True, 'featured.png'),
            ('IMDB Bottom 250', 'bottom_250', True, 'featured.png'),
            ('IMDB Bottom 1000', 'bottom_1000', True, 'featured.png')
            ]
            for i in awards: self.list.append(
            {
                'name': str(i[0]),
                'url': self.award_link % i[1] if i[2] else self.clear_link % i[1],
                'image': i[3],
                'action': 'movies'
            })
            
            self.addDirectory(self.list)
            return self.list

    def countryoforigin(self):
        countries = [
            ('Australien', 'au', True, 'languages.png'),
            ('Belgien', 'be', True, 'languages.png'),
            ('China', 'cn', True, 'languages.png'),
            ('Deutschland', 'de', True, 'languages.png'),
            ('Finnland', 'fi', True, 'languages.png'),
            ('Frankreich', 'fr', True, 'languages.png'),
            ('Großbritannien', 'gb', True, 'languages.png'),
            ('Indien', 'in', True, 'languages.png'),
            ('Israel', 'il', True, 'languages.png'),
            ('Italien', 'it', True, 'languages.png'),
            ('Japan', 'jp', True, 'languages.png'),
            ('Neuseeland', 'nz', True, 'languages.png'),
            ('Nigeria', 'ng', True, 'languages.png'),
            ('Norwegen', 'no', True, 'languages.png'),
            ('Russland', 'ru', True, 'languages.png'),
            ('Schweden', 'se', True, 'languages.png'),
            ('Schweiz', 'ch', True, 'languages.png'),
            ('Spanien', 'es', True, 'languages.png'),
            ('Südkorea', 'kr', True, 'languages.png'),
            ('Tschechische Republik', 'cz', True, 'languages.png'),
            ('USA', 'us', True, 'languages.png'),
            ('Österreich', 'at', True, 'languages.png')
            ]
        for i in countries: self.list.append(
            {
                'name': str(i[0]),
                'url': self.countryoforigin_link % i[1] if i[2] else self.clear_link % i[1],
                'image': i[3],
                'action': 'movies'
            })
            
        self.addDirectory(self.list)
        return self.list

    def certifications(self):
        certificates = [
        ('FSK - 0', '0'),
        ('FSK - 6', '6'),
        ('FSK - 12', '12'),
        ('FSK - 16', '16'),
        ('FSK - 18', '18'),
        ('Unbewertet', 'Unrated'),#Achtung Unrated ist nicht identisch zu Not+Rated!
        ('SPIO / JK', 'Not+Rated'),
        ('BPjM / Indiziert', 'BPjM+Restricted')
        ]

        for i in certificates: self.list.append({'name': str(i[0]), 'url': self.certification_link % str(i[1]), 'image': 'certificates.png', 'action': 'movies'})
        self.addDirectory(self.list)
        return self.list
        
    def studios(self):
        studios = [
        ('20th Century Fox', 'fox', 'century_fox.png'),
        ('Dreamworks', 'dreamworks', 'dreamworks.png'),
        ('MGM', 'mgm', 'mgm.png'),
        ('Paramount', 'paramount', 'paramount.png'),
        ('Sony', 'sony', 'sony.png'),
        ('Universal', 'universal', 'universal.png'),
        ('Walt Disney', 'disney', 'disney.png'),
        ('Warner Bros.', 'warner', 'warner_bros.png'),
        ]
        
        for i in studios: self.list.append({'name': str(i[0]), 'url': self.studio_link % str(i[1]), 'image': str(i[2]), 'action': 'movies'})
        self.addDirectory(self.list)
        return self.list


    def years(self):
        year = (self.datetime.strftime('%Y'))

        for i in range(int(year)-0, 1900, -1): self.list.append({'name': str(i), 'url': self.year_link % (str(i), str(i), "1"), 'image': 'years.png', 'action': 'movies'})
        self.addDirectory(self.list)
        return self.list


    def persons(self, url):
        if url == None:
            self.list = cache.get(self.imdb_person_list, 24, self.personlist_link)
        else:
            self.list = cache.get(self.imdb_person_list, 1, url)

        for i in range(0, len(self.list)): self.list[i].update({'action': 'movies'})
        if self.list == None or len(self.list) == 0:
            control.idle()
            control.infoDialog("Nichts gefunden", time=8000)
        else:
            self.addDirectory(self.list)
        return self.list


    def userlists(self):
        try:
            userlists = []
            if trakt.getTraktCredentialsInfo() == False: raise Exception()
            activity = trakt.getActivity()
        except:
            pass

        try:
            if trakt.getTraktCredentialsInfo() == False: raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user): raise Exception()
                userlists += cache.get(self.trakt_user_list, 720, self.traktlists_link, self.trakt_user)
            except:
                userlists += cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
        except:
            pass
        try:
            self.list = []
            if self.imdb_user == '': raise Exception()
            userlists += cache.get(self.imdb_user_list, 0, self.imdblists_link)
        except:
            pass
        try:
            self.list = []
            if trakt.getTraktCredentialsInfo() == False: raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user): raise Exception()
                userlists += cache.get(self.trakt_user_list, 720, self.traktlikedlists_link, self.trakt_user)
            except:
                userlists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
        except:
            pass

        self.list = userlists
        for i in range(0, len(self.list)): self.list[i].update({'image': 'userlists.png', 'action': 'movies'})
        self.addDirectory(self.list, queue=True)
        return self.list


    def trakt_list(self, url, user):
        from resources.lib.modules import client
        try:
            q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            q.update({'extended': 'full'})
            q = (urllib.urlencode(q)).replace('%2C', ',')
            u = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q

            result = trakt.getTraktAsJson(u)

            items = []
            for i in result:
                try: items.append(i['movie'])
                except: pass
            if len(items) == 0:
                items = result
        except:
            return

        try:
            q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            if not int(q['limit']) == len(items): raise Exception()
            q.update({'page': str(int(q['page']) + 1)})
            q = (urllib.urlencode(q)).replace('%2C', ',')
            next = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = item['title']
                title = client.replaceHTMLCodes(title)

                year = item['year']
                year = re.sub('[^0-9]', '', str(year))

                if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

                imdb = item['ids']['imdb']
                log_utils.log('MovieShit - trakt_list - imdb: ' + str(imdb))
                if imdb == None or imdb == '': raise Exception()
                imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

                tmdb = str(item.get('ids', {}).get('tmdb', 0))

                try: premiered = item['released']
                except: premiered = '0'
                try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
                except: premiered = '0'

                try: genre = item['genres']
                except: genre = '0'
                genre = [i.title() for i in genre]
                if genre == []: genre = '0'
                genre = ' / '.join(genre)

                try: duration = str(item['runtime'])
                except: duration = '0'
                if duration == None: duration = '0'

                try: rating = str(item['rating'])
                except: rating = '0'
                if rating == None or rating == '0.0': rating = '0'

                try: votes = str(item['votes'])
                except: votes = '0'
                try: votes = str(format(int(votes),',d'))
                except: pass
                if votes == None: votes = '0'

                try: mpaa = item['certification']
                except: mpaa = '0'
                if mpaa == None: mpaa = '0'

                try: plot = item['overview']
                except: plot = '0'
                if plot == None: plot = '0'
                plot = client.replaceHTMLCodes(plot)

                try: tagline = item['tagline']
                except: tagline = '0'
                if tagline == None: tagline = '0'
                tagline = client.replaceHTMLCodes(tagline)

                self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot, 'tagline': tagline, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': '0', 'next': next})
            except:
                pass

        return self.list


    def trakt_user_list(self, url, user):
        from resources.lib.modules import client
        try:
            items = trakt.getTraktAsJson(url)
        except:
            pass

        for item in items:
            try:
                try: name = item['list']['name']
                except: name = item['name']
                name = client.replaceHTMLCodes(name)

                try: url = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
                except: url = ('me', item['ids']['slug'])
                url = self.traktlist_link % url
                url = url.encode('utf-8')

                self.list.append({'name': name, 'url': url, 'context': url})
            except:
                pass

        self.list = sorted(self.list, key=lambda k: utils.title_key(k['name']))
        return self.list


    def imdb_list(self, url):
        from resources.lib.modules import client
        try:
            for i in re.findall('date\[(\d+)\]', url):
                url = url.replace('date[%s]' % i, (self.datetime - datetime.timedelta(days = int(i))).strftime('%Y-%m-%d'))

            def imdb_watchlist_id(url):
                return client.parseDOM(client.request(url), 'meta', ret='content', attrs = {'property': 'pageId'})[0]

            if url == self.imdbwatchlist_link:
                url = cache.get(imdb_watchlist_id, 8640, url)
                url = self.imdblist_link % url

            elif url == self.imdbwatchlist2_link:
                url = cache.get(imdb_watchlist_id, 8640, url)
                url = self.imdblist2_link % url

            result = client.request(url)

            result = result.replace('\n', ' ')

            items = client.parseDOM(result, 'div', attrs = {'class': 'lister-item .+?'})
            items += client.parseDOM(result, 'div', attrs = {'class': 'list_item.+?'})
        except:
            return

        try:
            next = client.parseDOM(result, 'a', ret='href', attrs = {'class': 'lister-page-next .+?'})
            if len(next) == 0:
                next = client.parseDOM(result, 'a', ret='href', attrs = {'class': '.+?lister-page-next .+?'})

            if len(next) == 0:
                next = client.parseDOM(result, 'div', attrs = {'class': 'list-pagination'})[0]
                next = zip(client.parseDOM(next, 'a', ret='href'), client.parseDOM(next, 'a'))
                next = [i[0] for i in next if 'Next' in i[1]]

            next = url.replace(urlparse.urlparse(url).query, urlparse.urlparse(next[0]).query)
            next = client.replaceHTMLCodes(next)
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = client.parseDOM(item, 'a')[1]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                year = client.parseDOM(item, 'span', attrs = {'class': 'lister-item-year.+?'})
                year += client.parseDOM(item, 'span', attrs = {'class': 'year_type'})
                try: year = re.compile('(\d{4})').findall(year)[0]
                except: year = '0'
                year = year.encode('utf-8')

                if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

                imdb = client.parseDOM(item, 'a', ret='href')[0]
                imdb = re.findall('(tt\d*)', imdb)[0]
                imdb = imdb.encode('utf-8')

                try: poster = client.parseDOM(item, 'img', ret='loadlate')[0]
                except: poster = '0'
                if '/nopicture/' in poster: poster = '0'
                poster = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', poster)
                poster = client.replaceHTMLCodes(poster)
                poster = poster.encode('utf-8')

                try: genre = client.parseDOM(item, 'span', attrs = {'class': 'genre'})[0]
                except: genre = '0'
                genre = ' / '.join([i.strip() for i in genre.split(',')])
                if genre == '': genre = '0'
                genre = client.replaceHTMLCodes(genre)
                genre = genre.encode('utf-8')

                try: duration = re.findall('(\d+?) min(?:s|)', item)[-1]
                except: duration = '0'
                duration = duration.encode('utf-8')

                rating = '0'
                try: rating = client.parseDOM(item, 'span', attrs = {'class': 'rating-rating'})[0]
                except: pass
                try: rating = client.parseDOM(rating, 'span', attrs = {'class': 'value'})[0]
                except: rating = '0'
                try: rating = client.parseDOM(item, 'div', ret='data-value', attrs = {'class': '.*?imdb-rating'})[0]
                except: pass
                if rating == '' or rating == '-': rating = '0'
                rating = client.replaceHTMLCodes(rating)
                rating = rating.encode('utf-8')

                try: votes = client.parseDOM(item, 'div', ret='title', attrs = {'class': '.*?rating-list'})[0]
                except: votes = '0'
                try: votes = re.findall('\((.+?) vote(?:s|)\)', votes)[0]
                except: votes = '0'
                if votes == '': votes = '0'
                votes = client.replaceHTMLCodes(votes)
                votes = votes.encode('utf-8')

                try: mpaa = client.parseDOM(item, 'span', attrs = {'class': 'certificate'})[0]
                except: mpaa = '0'
                if mpaa == '' or mpaa == 'NOT_RATED': mpaa = '0'
                mpaa = mpaa.replace('_', '-')
                mpaa = client.replaceHTMLCodes(mpaa)
                mpaa = mpaa.encode('utf-8')

                try: director = re.findall('Director(?:s|):(.+?)(?:\||</div>)', item)[0]
                except: director = '0'
                director = client.parseDOM(director, 'a')
                director = ' / '.join(director)
                if director == '': director = '0'
                director = client.replaceHTMLCodes(director)
                director = director.encode('utf-8')

                try: cast = re.findall('Stars(?:s|):(.+?)(?:\||</div>)', item)[0]
                except: cast = '0'
                cast = client.replaceHTMLCodes(cast)
                cast = cast.encode('utf-8')
                cast = client.parseDOM(cast, 'a')
                if cast == []: cast = '0'

                plot = '0'
                try: plot = client.parseDOM(item, 'p', attrs = {'class': 'text-muted'})[0]
                except: pass
                try: plot = client.parseDOM(item, 'div', attrs = {'class': 'item_description'})[0]
                except: pass
                plot = plot.rsplit('<span>', 1)[0].strip()
                plot = re.sub('<.+?>|</.+?>', '', plot)
                if plot == '': plot = '0'
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                self.list.append({'title': title, 'originaltitle': title, 'year': year, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'cast': cast, 'plot': plot, 'tagline': '0', 'imdb': imdb, 'tmdb': '0', 'tvdb': '0', 'poster': poster, 'next': next})
            except:
                pass

        return self.list


    def imdb_person_list(self, url):
        from resources.lib.modules import client
        try:
            result = client.request(url)
            items = client.parseDOM(result, 'div', attrs = {'class': '.+? mode-detail'})
        except:
            return

        for item in items:
            try:
                name = client.parseDOM(item, 'img', ret='alt')[0]
                name = client.replaceHTMLCodes(name)
                name = name.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.findall('(nm\d*)', url, re.I)[0]
                url = self.person_link % url
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='src')[0]
                #if not ('._SX' in image or '._SY' in image): raise Exception()
                #image = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'name': name, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def imdb_user_list(self, url):
        from resources.lib.modules import client
        try:
            result = client.request(url)
            items = client.parseDOM(result, 'li', attrs = {'class': 'ipl-zebra-list__item user-list'})
        except:
            pass

        for item in items:
            try:
                name = client.parseDOM(item, 'a')[0]
                name = client.replaceHTMLCodes(name)
                name = name.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = url.split('/list/', 1)[-1].strip('/')
                url = self.imdblist_link % url
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                self.list.append({'name': name, 'url': url, 'context': url})
            except:
                pass

        self.list = sorted(self.list, key=lambda k: utils.title_key(k['name']))
        return self.list


    def worker(self, level=1):
        self.meta = []
        total = len(self.list)

        self.fanart_tv_headers = {'api-key': 'NDZkZmMyN2M1MmE0YTc3MjY3NWQ4ZTMyYjdiY2E2OGU='.decode('base64')}
        if not self.fanart_tv_user == '':
            self.fanart_tv_headers.update({'client-key': self.fanart_tv_user})

        for i in range(0, total): self.list[i].update({'metacache': False})

        self.list = metacache.fetch(self.list, self.lang, self.user)

        for r in range(0, total, 40):
            threads = []
            for i in range(r, r+40):
                if i <= total: threads.append(workers.Thread(self.super_info, i))
            [i.start() for i in threads]
            [i.join() for i in threads]

            if self.meta: metacache.insert(self.meta)

        self.list = [i for i in self.list if not i['imdb'] == '0']        

        if self.fanart_tv_user == '':
            for i in self.list: i.update({'clearlogo': '0', 'clearart': '0'})


    def super_info(self, i):
        from resources.lib.modules import client
        try:
            if self.list[i]['metacache'] == True: raise Exception()

            imdb = self.list[i]['imdb']

            item = trakt.getMovieSummary(imdb)

            title = item.get('title')
            title = client.replaceHTMLCodes(title)

            originaltitle = title

            year = item.get('year', 0)
            year = re.sub('[^0-9]', '', str(year))

            imdb = item.get('ids', {}).get('imdb', '0')
            imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

            tmdb = str(item.get('ids', {}).get('tmdb', 0))

            premiered = item.get('released', '0')
            try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
            except: premiered = '0'

            genre = item.get('genres', [])
            genre = [x.title() for x in genre]
            genre = ' / '.join(genre).strip()
            if not genre: genre = '0'

            duration = str(item.get('Runtime', 0))

            rating = item.get('rating', '0')
            if not rating or rating == '0.0': rating = '0'

            votes = item.get('votes', '0')
            try: votes = str(format(int(votes), ',d'))
            except: pass

            mpaa = item.get('certification', '0')
            if not mpaa: mpaa = '0'

            tagline = item.get('tagline', '0')

            plot = item.get('overview', '0')

            people = trakt.getPeople(imdb, 'movies')

            director = writer = ''
            if 'crew' in people and 'directing' in people['crew']:
                director = ', '.join([director['person']['name'] for director in people['crew']['directing'] if director['job'].lower() == 'director'])
            if 'crew' in people and 'writing' in people['crew']:
                writer = ', '.join([writer['person']['name'] for writer in people['crew']['writing'] if writer['job'].lower() in ['writer', 'screenplay', 'author']])

            cast = []
            for person in people.get('cast', []):
                cast.append({'name': person['person']['name'], 'role': person['character']})
            cast = [(person['name'], person['role']) for person in cast]

            try:
                if self.lang == 'en' or self.lang not in item.get('available_translations', [self.lang]): raise Exception()

                trans_item = trakt.getMovieTranslation(imdb, self.lang, full=True)

                title = trans_item.get('title') or title
                tagline = trans_item.get('tagline') or tagline
                plot = trans_item.get('overview') or plot
            except:
                pass

            try:
                artmeta = True
                #if self.fanart_tv_user == '': raise Exception()
                art = client.request(self.fanart_tv_art_link % imdb, headers=self.fanart_tv_headers, timeout='10', error=True)
                try: art = json.loads(art)
                except: artmeta = False
            except:
                pass

            try:
                poster2 = art['movieposter']
                poster2 = [x for x in poster2 if x.get('lang') == self.lang][::-1] + [x for x in poster2 if x.get('lang') == 'en'][::-1] + [x for x in poster2 if x.get('lang') in ['00', '']][::-1]

                posterlist_fanarttv = []
                
                for index,entry in enumerate(poster2):                    
                    posterlist_fanarttv.append(entry['url'].encode('utf-8'))
                
                poster2 = posterlist_fanarttv                
                
            except:
                poster2 = '0'

            try:
                if 'moviebackground' in art: fanart = art['moviebackground']
                else: fanart = art['moviethumb']
                fanart = [x for x in fanart if x.get('lang') == self.lang][::-1] + [x for x in fanart if x.get('lang') == 'en'][::-1] + [x for x in fanart if x.get('lang') in ['00', '']][::-1]

                bglist_fanarttv = []                

                for index,entry in enumerate(fanart):                    
                    bglist_fanarttv.append(entry['url'].encode('utf-8'))

                fanart = bglist_fanarttv

                #fanart = fanart[0]['url'].encode('utf-8')
            except:
                fanart = '0'

            try:
                banner = art['moviebanner']
                banner = [x for x in banner if x.get('lang') == self.lang][::-1] + [x for x in banner if x.get('lang') == 'en'][::-1] + [x for x in banner if x.get('lang') in ['00', '']][::-1]
                banner = banner[0]['url'].encode('utf-8')
            except:
                banner = '0'

            try:
                if 'hdmovielogo' in art: clearlogo = art['hdmovielogo']
                else: clearlogo = art['clearlogo']
                clearlogo = [x for x in clearlogo if x.get('lang') == self.lang][::-1] + [x for x in clearlogo if x.get('lang') == 'en'][::-1] + [x for x in clearlogo if x.get('lang') in ['00', '']][::-1]
                clearlogo = clearlogo[0]['url'].encode('utf-8')
            except:
                clearlogo = '0'

            try:
                if 'hdmovieclearart' in art: clearart = art['hdmovieclearart']
                else: clearart = art['clearart']
                clearart = [x for x in clearart if x.get('lang') == self.lang][::-1] + [x for x in clearart if x.get('lang') == 'en'][::-1] + [x for x in clearart if x.get('lang') in ['00', '']][::-1]
                clearart = clearart[0]['url'].encode('utf-8')
            except:
                clearart = '0'

            try:
                if self.tm_user == '': raise Exception()

                art2 = client.request(self.tm_art_link % imdb, timeout='10', error=True)
                art2 = json.loads(art2)
            except:
                pass

            try:
                poster3 = art2['posters']
                poster3 = [x for x in poster3 if x.get('iso_639_1') == self.lang] + [x for x in poster3 if x.get('iso_639_1') == 'en'] + [x for x in poster3 if x.get('iso_639_1') not in [self.lang, 'en']]
                poster3 = [(x['width'], x['file_path']) for x in poster3]
                poster3 = [(x[0], x[1]) if x[0] < 300 else ('300', x[1]) for x in poster3]

                posterlist_tmdb = []
                
                for indexz,entryz in enumerate(poster3):
                    posterlist_tmdb.append((self.tm_img_link % entryz).encode('utf-8'))
                                
                #poster3 = self.tm_img_link % poster3[0]
                #poster3 = poster3.encode('utf-8')
                poster3=posterlist_tmdb                
            except:
                poster3 = '0'

            try:
                fanart2 = art2['backdrops']
                fanart2 = [x for x in fanart2 if x.get('iso_639_1') == self.lang] + [x for x in fanart2 if x.get('iso_639_1') == 'en'] + [x for x in fanart2 if x.get('iso_639_1') not in [self.lang, 'en']]
                fanart2 = [x for x in fanart2 if x.get('width') == 1920] + [x for x in fanart2 if x.get('width') < 1920]
                fanart2 = [(x['width'], x['file_path']) for x in fanart2]
                fanart2 = [(x[0], x[1]) if x[0] < 1280 else ('1280', x[1]) for x in fanart2]

                bglist_tmdb = []
                
                for indexz,entryz in enumerate(fanart2):                    
                    bglist_tmdb.append((self.tm_img_link % entryz).encode('utf-8'))                   

                fanart2 = bglist_tmdb
                
                #fanart2 = self.tm_img_link % fanart2[0]
                #fanart2 = fanart2.encode('utf-8')
            except:
                fanart2 = '0'

            item = {'title': title, 'originaltitle': originaltitle, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'poster': '0', 'poster2': poster2, 'poster3': poster3, 'banner': banner, 'fanart': fanart, 'fanart2': fanart2, 'clearlogo': clearlogo, 'clearart': clearart, 'premiered': premiered, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline}
            item = dict((k,v) for k, v in item.iteritems() if not v == '0')
            self.list[i].update(item)    

            if artmeta == False: raise Exception()

            meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.user, 'item': item,'poster':{"tmdb":"0"},'background':{"tmdb":"0"}}
            self.meta.append(meta)
        except:
            pass


    def movieDirectory(self, items):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]

        syshandle = int(sys.argv[1])

        addonPoster, addonBanner = control.addonPoster(), control.addonBanner()

        addonFanart, settingFanart = control.addonFanart(), control.setting('fanart')

        traktCredentials = trakt.getTraktCredentialsInfo()

        try: isOld = False ; control.item().getArt('type')
        except: isOld = True

        isPlayable = 'true' if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'

        indicators = playcount.getMovieIndicators(refresh=True) if action == 'movies' else playcount.getMovieIndicators()

        playbackMenu = "Abspielen mit..." if control.setting('hosts.mode') == '2' else "Autoplay"

        watchedMenu = "In Trakt [I]Gesehen[/I]" if trakt.getTraktIndicatorsInfo() == True else "In Lastship [I]Gesehen[/I]"

        unwatchedMenu = "In Trakt [I]Ungesehen[/I]" if trakt.getTraktIndicatorsInfo() == True else "In Lastship [I]Ungesehen[/I]"

        queueMenu = "Zur Warteschlange hinzufügen"
        
        traktManagerMenu = "[B]Trakt-Manager[/B]"

        nextMenu = "Nächste Seite"

        addToLibrary = "Zur Bibliothek hinzufügen"

        for i in items:
            try:
                label = '%s (%s)' % (i['title'], i['year'])
                imdb, tmdb, title, year = i['imdb'], i['tmdb'], i['originaltitle'], i['year']
                sysname = urllib.quote_plus('%s (%s)' % (title, year))
                systitle = urllib.quote_plus(title)

                meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
                meta.update({'code': imdb, 'imdbnumber': imdb, 'imdb_id': imdb})
                meta.update({'tmdb_id': tmdb})
                meta.update({'mediatype': 'movie'})
                meta.update({'trailer': '%s?action=trailer&name=%s' % (sysaddon, urllib.quote_plus(label))})
                #meta.update({'trailer': 'plugin://script.extendedinfo/?info=playtrailer&&id=%s' % imdb})
                if not 'duration' in i: meta.update({'duration': '120'})
                elif i['duration'] == '0': meta.update({'duration': '120'})
                try: meta.update({'duration': str(int(meta['duration']) * 60)})
                except: pass
                try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
                except: pass

                 # Poster FanArt select ##
                posterdb=metacache.fetchfanart(meta['imdb'],"poster")                
                backgroundb=metacache.fetchfanart(meta['imdb'],"background")
                
                poster_fanart = i.get("poster2","")
                poster_tmdb = i.get("poster3","")
                
                poster_count_fanart=len(poster_fanart)
                poster_count_tmdb=len(poster_tmdb)

                background_fanart = i.get("fanart","")
                background_tmdb = i.get("fanart2","")

                bg_count_fanart=len(background_fanart)
                bg_count_tmdb=len(background_tmdb)

                for key, value in posterdb.iteritems():
                    if key=='tmdb':                        
                        poster=poster_tmdb[int(posterdb['tmdb'])]

                    if key=='fanart':                        
                        poster=poster_fanart[int(posterdb['fanart'])]
                    
                
                for key, value in backgroundb.iteritems():
                    if key=='tmdb':                        
                        background=background_tmdb[int(backgroundb['tmdb'])]

                    if key=='fanart':                        
                        background=background_fanart[int(backgroundb['fanart'])]
    

                ## Fallback ##
                if background == "0": background=addonFanart
                if poster == "0": poster=addonPoster
                
                ## /Poster FanArt select ##                

                meta.update({'poster': poster})

                sysmeta = urllib.quote_plus(json.dumps(meta))

                url = '%s?action=play&title=%s&year=%s&imdb=%s&meta=%s&t=%s' % (sysaddon, systitle, year, imdb, sysmeta, self.systime)
                sysurl = urllib.quote_plus(url)

                cm = []

                if control.setting('cm.addtolibrary') == 'true':
                    cm.append((addToLibrary, 'RunPlugin(%s?action=movieToLibrary&name=%s&title=%s&year=%s&imdb=%s&tmdb=%s)' % (sysaddon, sysname, systitle, year, imdb, tmdb)))
                else:
                    pass
                if control.setting('cm.queue') == 'true':
                    cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
                else:
                    pass
                     
                try:
                    overlay = int(playcount.getMovieOverlay(indicators, imdb))
                    if overlay == 7:
                        cm.append((unwatchedMenu, 'RunPlugin(%s?action=moviePlaycount&imdb=%s&query=6)' % (sysaddon, imdb)))
                        meta.update({'playcount': 1, 'overlay': 7})
                    else:
                        cm.append((watchedMenu, 'RunPlugin(%s?action=moviePlaycount&imdb=%s&query=7)' % (sysaddon, imdb)))
                        meta.update({'playcount': 0, 'overlay': 6})
                except:
                    pass

                if control.setting('cm.similiar') == 'true':
                    cm.append(("Finde Ähnliches", 'ActivateWindow(10025,%s?action=movies&url=https://api.trakt.tv/movies/%s/related,return)' % (sysaddon, imdb)))
                else:
                    pass
                if control.setting('cm.poster') == 'true':
                    cm.append(("Poster auswählen",  'RunPlugin(%s?action=select_fanart&arttype=%s&imdb=%s&count_tmdb=%s&count_fanart=%s)' % (sysaddon,"poster",imdb,poster_count_tmdb,poster_count_fanart)))
                else:
                    pass
                if control.setting('cm.fanart') == 'true':
                    cm.append(("Fanart auswählen", 'RunPlugin(%s?action=select_fanart&arttype=%s&imdb=%s&count_tmdb=%s&count_fanart=%s)' % (sysaddon,"background",imdb,bg_count_tmdb,bg_count_fanart)))
                else:
                    pass
                if control.setting('cm.traktmanager') == 'true':
                    if traktCredentials == True:
                        cm.append((traktManagerMenu, 'RunPlugin(%s?action=traktManager&name=%s&imdb=%s&content=movie)' % (sysaddon, sysname, imdb)))
                else:
                    pass
                if control.setting('cm.playback') == 'true':
                    cm.append((playbackMenu, 'RunPlugin(%s?action=alterSources&url=%s&meta=%s)' % (sysaddon, sysurl, sysmeta)))
                else:
                    pass

                if isOld == True:
                    cm.append((control.lang2(19033).encode('utf-8'), 'Action(Info)')) #Zur Bibliothek hinzufügen

                item = control.item(label=label)
                art = {}
                art.update({'icon': poster, 'thumb': poster, 'poster': poster})

                if 'banner' in i and not i['banner'] == '0':
                    art.update({'banner': i['banner']})
                else:
                    art.update({'banner': addonBanner})

                if 'clearlogo' in i and not i['clearlogo'] == '0':
                    art.update({'clearlogo': i['clearlogo']})

                if 'clearart' in i and not i['clearart'] == '0':
                    art.update({'clearart': i['clearart']})

                item.setProperty('Fanart_Image', background)
                item.setArt(art)
                item.addContextMenuItems(cm)
                item.setProperty('IsPlayable', isPlayable)
                
                meta.pop('fanart2', None)
                meta.pop('imdb', None)
                meta.pop('imdb_id', None)
                meta.pop('metacache', None)
                meta.pop('next', None)
                meta.pop('poster', None)
                meta.pop('poster3', None)
                meta.pop('tmdb', None)
                meta.pop('tmdb_id', None)
                
                item.setInfo(type='Video', infoLabels = meta)
                video_streaminfo = {'codec': 'h264'}
                item.addStreamInfo('video', video_streaminfo)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
            except:
                pass

        try:
            url = items[0]['next']
            if url == '': raise Exception()

            icon = control.addonNext()
            url = '%s?action=moviePage&url=%s' % (sysaddon, urllib.quote_plus(url))

            item = control.item(label=nextMenu)

            item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'banner': icon})
            if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
        except:
            pass

        control.content(syshandle, 'movies')
        control.directory(syshandle, cacheToDisc=True)
        control.sleep(200)
        views.setView('movies', {'skin.estuary': 55, 'skin.confluence': 500})


    def addDirectory(self, items, queue=False):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]

        syshandle = int(sys.argv[1])

        addonFanart, addonThumb, artPath = control.addonFanart(), control.addonThumb(), control.artPath()
        
        playRandom = "Zufallswiedergabe"

        queueMenu = "Zur Warteschlange hinzufügen"

        addToLibrary = "Zur Bibliothek hinzufügen"

        for i in items:
            try:
                name = i['name']

                if i['image'].startswith('http'): thumb = i['image']
                elif not artPath == None: thumb = os.path.join(artPath, i['image'])
                else: thumb = addonThumb

                url = '%s?action=%s' % (sysaddon, i['action'])
                try: url += '&url=%s' % urllib.quote_plus(i['url'])
                except: pass

                cm = []
                
                cm.append((playRandom, 'RunPlugin(%s?action=random&rtype=movie&url=%s)' % (sysaddon, urllib.quote_plus(i['url']))))

                if queue == True:
                    cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))

                try: cm.append((addToLibrary, 'RunPlugin(%s?action=moviesToLibrary&url=%s)' % (sysaddon, urllib.quote_plus(i['context']))))
                except: pass

                item = control.item(label=name)

                item.setArt({'icon': thumb, 'thumb': thumb})
                if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

                item.addContextMenuItems(cm)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
            except:
                pass

        control.content(syshandle, 'addons')
        control.directory(syshandle, cacheToDisc=True)
