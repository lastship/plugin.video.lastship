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


import time

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

from resources.lib.modules import control
import json

def fetchfanartlist(imdb,arttype):
    try:        
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT item FROM meta WHERE imdb = '%s'" % imdb)
        result = dbcur.fetchone()
        
        import ast
        
        if arttype=="poster":
            
            try:
                # use ast import due to unicode. limit each list to max of 20 entries neeid to crosscheck against count_tmdb                
                plist_tmdb=ast.literal_eval(result[0])['poster3']
                plist_tmdb=plist_tmdb[:20]
            except:
                plist_tmdb=[]

            
            try:
                plist_fanart=ast.literal_eval(result[0])['poster2']
                plist_fanart=plist_fanart[:20]
            except:                
                plist_fanart=[]
            
        elif arttype=="background":
            # use ast import due to unicode. limit each list to max of 20 entries neeid to crosscheck against count_tmdb
            try:
                plist_tmdb=ast.literal_eval(result[0])['fanart2']
                plist_tmdb=plist_tmdb[:20]
            except:
                plist_tmdb=[]
            try:
                plist_fanart=ast.literal_eval(result[0])['fanart']
                plist_fanart=plist_fanart[:20]
            except:
                plist_fanart=[]
            
        posterlist=plist_tmdb+plist_fanart
        
        return posterlist
    except:
        return

def fetchfanart(imdb,arttype):
    try:        
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT poster,background FROM meta WHERE imdb = '%s'" % imdb)
        result = dbcur.fetchone()        
        match = [x[0] for x in result]        
        if arttype == "poster":
            return json.loads(result[0])
        elif arttype == "background":            
            return json.loads(result[1])
    except:
        return

def setfanart(arttype,imdb,fanartid,scraperinfo):
    try:
        # fanartid sollte gleich als string übergeben werden #        
        dbcon = database.connect(control.metacacheFile)        
        dbcur = dbcon.cursor()        
        if arttype=="poster":            
            dbcur.execute("update meta set poster='%s' WHERE imdb = '%s'" % (json.dumps({scraperinfo:str(fanartid)}),imdb))
        elif arttype=="background":            
            dbcur.execute("update meta set background='%s' WHERE imdb = '%s'" % (json.dumps({scraperinfo:str(fanartid)}),imdb))

        dbcon.commit()        
    except:
        return
    

def fetch(items, lang='de', user=''):
    try:
        t2 = int(time.time())
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
    except:
        return items

    for i in range(0, len(items)):
        try:
            dbcur.execute("SELECT * FROM meta WHERE (imdb = '%s' and lang = '%s' and user = '%s' and not imdb = '0') or (tvdb = '%s' and lang = '%s' and user = '%s' and not tvdb = '0')" % (items[i]['imdb'], lang, user, items[i]['tvdb'], lang, user))
            match = dbcur.fetchone()

            
            ## Vorsicht Hardcoded match[] werte, müssen mit TB Tabelle item & zeit übereinstimmen##
            t1 = int(match[7])
            update = (abs(t2 - t1) / 3600) >= 720
            if update == True: raise Exception()

            item = eval(match[6].encode('utf-8'))
            item = dict((k,v) for k, v in item.iteritems() if not v == '0')

            items[i].update(item)
            items[i].update({'metacache': True})
        except:
            pass

    return items


def insert(meta):
    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS meta (""imdb TEXT, ""tvdb TEXT, ""lang TEXT, ""user TEXT, ""poster TEXT,""background TEXT, ""item TEXT, ""time TEXT, ""UNIQUE(imdb, tvdb, lang, user)"");")
        t = int(time.time())
        for m in meta:            
            try:
                # Fanart als Liste fanar.tv/tmdb, posterid,backgroundid
                if not "user" in m: m["user"] = ''
                if not "lang" in m: m["lang"] = 'de'
                i = repr(m['item'])
                try: dbcur.execute("DELETE * FROM meta WHERE (imdb = '%s' and lang = '%s' and user = '%s' and not imdb = '0') or (tvdb = '%s' and lang = '%s' and user = '%s' and not tvdb = '0')" % (m['imdb'], m['lang'], m['user'], m['tvdb'], m['lang'], m['user']))
                except: pass
                dbcur.execute("INSERT INTO meta Values (?, ?, ?, ?, ?, ?, ?, ?)", (m['imdb'], m['tvdb'], m['lang'], m['user'],json.dumps(m['poster']),json.dumps(m['background']), i, t))
            except:
                pass

        dbcon.commit()
    except:
        return
