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
import datetime
import cache
import base64
from resources.lib.modules import control


try:
    from sqlite3 import dbapi2 as db, OperationalError
except ImportError:
    from pysqlite2 import dbapi2 as db, OperationalError

faultTable = "faultLog"

######### Tags
tagSearch = "SEARCH"
tagResolve = "RESOLVE"
tagScrape = "SCRAPE"
tagDisabled = "DISABLED"

######### Settings
try: maxFaultsPerDay = int(control.setting('FaultLogger.numErrors'))
except: maxFaultsPerDay = 10

try: hoursTillRecheck = int(control.setting('FaultLogger.recheckHours'))
except: hoursTillRecheck = 24
triggerCacheSetting = "source_fault_last_seen"

statisticURL = "aHR0cHM6Ly9sYXN0c2hpcC5jaC9Db3VudGVyL3Byb3ZpZGVyY291bnQucGhwP3NpdGU9JXMmZXhwaXJlPSVkJnNldA=="


def init():
    now = int(time.time())
    timelimit = now - 60*60*hoursTillRecheck
    lastSeen = cache.cache_get(triggerCacheSetting)
    if lastSeen is not None and int(lastSeen["value"]) > timelimit:
        return

    try:
        dbcon = db.connect(control.providercacheFile)
        dbcur = dbcon.cursor()
        dbcur.executescript("CREATE TABLE IF NOT EXISTS %s (ID Integer PRIMARY KEY AUTOINCREMENT, provider TEXT, tag TEXT, date INTEGER, info TEXT);" % faultTable)
        dbcur.execute("DELETE FROM %s WHERE date < ?;" % faultTable, (timelimit,))
        try:
            dbcur.execute("SELECT info FROM %s" % faultTable)
        except:
            dbcur.executescript("ALTER Table %s ADD info TEXT" % faultTable)
        dbcon.commit()
        dbcur.close()
        del dbcur
        dbcon.close()
    except:
        pass

    cache.cache_insert(triggerCacheSetting, now)


def logFault(provider, tag, additional_info=""):
    now = int(time.time())
    try:
        dbcon = db.connect(control.providercacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("INSERT INTO %s VALUES (null,?,?,?,?)" % faultTable, (provider, tag, now, additional_info))
        dbcon.commit()
        dbcur.execute("SELECT COUNT(*) FROM %s WHERE provider=? AND tag <> ? " % faultTable, (provider, tagDisabled))
        num_latest_faults = dbcur.fetchone()[0]
        if num_latest_faults >= maxFaultsPerDay:
            dbcur.execute("INSERT INTO %s VALUES (null,?,?,?,?)" % faultTable, (provider, tagDisabled, now, additional_info))
            dbcon.commit()
            from resources.lib.modules import client
            temp = '%s-%s' % (provider, tag)
            if additional_info != "":
                temp = '%s-%s-%s' % (provider, tag, additional_info)
            client.request(base64.b64decode(statisticURL) % (temp, now+hoursTillRecheck*60*60))
        dbcur.close()
        del dbcur
        dbcon.close()
    except:
        pass
    return


def isEnabled(provider):
    try:
        dbcon = db.connect(control.providercacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT COUNT(*) FROM %s WHERE provider=? AND tag = ?" % faultTable,
                      (provider, tagDisabled))
        numDisabled = dbcur.fetchone()[0]
        dbcur.close()
        del dbcur
        dbcon.close()
        if numDisabled > 0:
            return False
    except:
        return True
    return True


def getFaultInfoString():
    faults = getFaults()
    if faults is None or len(faults) == 0 : return "Keine";

    info = ""

    for faultProvider in faults:
        fptime = datetime.datetime.fromtimestamp(faultProvider[2]).strftime('%d.%m.%Y %H:%M:%S')
        if faultProvider[3] == tagDisabled:
            info += "[COLOR red]"
        info += faultProvider[0] + ", "+str(faultProvider[1])+" mal, zuletzt: "+fptime
        if faultProvider[3] == tagDisabled:
            info += "[/COLOR]\n"
        else:
            info += ", tag: "+faultProvider[3]+"\n"

    return info


def getFaults():
    try:
        dbcon = db.connect(control.providercacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT provider, COUNT(provider), date, tag as faults FROM %s Group By provider Order By count(provider) DESC, date ASC" %faultTable)
        res = dbcur.fetchall()
        dbcur.close()
        del dbcur
        dbcon.close()
        return res
    except:
        return None
