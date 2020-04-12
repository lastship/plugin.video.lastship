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

import hashlib
import re
import time
from resources.lib.modules import control
import pickle

try:
    from sqlite3 import dbapi2 as db, OperationalError
except ImportError:
    from pysqlite2 import dbapi2 as db, OperationalError

"""
This module is used to get/set cache for every action done in the system
"""

cache_table = 'cache'

def get(function, duration, *args, **kwargs):
    # type: (function, int, object) -> object or None
    """
    Gets cached value for provided function with optional arguments, or executes and stores the result
    :param function: Function to be executed
    :param duration: Duration of validity of cache in hours
    :param args: Optional arguments for the provided function
    """

    try:
        key = _hash_function(function, args, kwargs)
        cache_result = cache_get(key)
        if cache_result:
            if _is_cache_valid(cache_result['date'], duration):
                return pickle.loads(cache_result['value'])
            else:
                cache_delete(key)

        fresh_result = function(*args, **kwargs)
        if not fresh_result:
            # If the cache is old, but we didn't get fresh result, return the old cache
            if cache_result:
                return cache_result
            return None

        cache_insert(key, pickle.dumps(fresh_result))

        return fresh_result
    except Exception:
        return None


def timeout(function, *args):
    try:
        key = _hash_function(function, args)
        result = cache_get(key)
        return int(result['date'])
    except Exception:
        return None


def cache_get(key):
    # type: (str, str) -> dict or None
    try:
        cursor = _get_connection_cursor()
        cursor.execute("SELECT * FROM %s WHERE key = ?" % cache_table, [key])
        return cursor.fetchone()
    except OperationalError:
        return None

def cache_delete(key):
    # type: (str, str) -> dict or None
    try:
        cursor = _get_connection_cursor()
        cursor.execute("DELETE FROM %s WHERE key = ?" % cache_table, [key])
        cursor.connection.commit()
    except OperationalError:
        return None

def cache_insert(key, value):
    # type: (str, str) -> None
    cursor = _get_connection_cursor()
    now = int(time.time())
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS %s (key TEXT, value TEXT, date INTEGER, UNIQUE(key))"
        % cache_table
    )
    update_result = cursor.execute(
        "UPDATE %s SET value=?,date=? WHERE key=?"
        % cache_table, (value, now, key))

    if update_result.rowcount is 0:
        cursor.execute(
            "INSERT INTO %s Values (?, ?, ?)"
            % cache_table, (key, value, now)
        )

    cursor.connection.commit()


def cache_clear():
    try:
        cursor = _get_connection_cursor()

        for t in [cache_table, 'rel_list', 'rel_lib']:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_meta():
    try:
        cursor = _get_connection_cursor_meta()

        for t in ['meta']:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_providers():
    try:
        cursor = _get_connection_cursor_providers()

        for t in ['rel_src', 'rel_url', 'faultLog']:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
        cache_insert("source_fault_last_seen","0")
    except:
        pass


def cache_clear_search():
    try:
        cursor = _get_connection_cursor_search()

        for t in ['tvshow', 'movies']:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_all():
    cache_clear()
    cache_clear_meta()
    cache_clear_providers()


def _get_connection_cursor():
    conn = _get_connection(control.cacheFile)
    conn.text_factory = str
    return conn.cursor()


def _get_connection(filename):
    control.makeFile(control.dataPath)
    conn = db.connect(filename)
    conn.row_factory = _dict_factory
    return conn


def _get_connection_cursor_meta():
    conn = _get_connection(control.metacacheFile)
    return conn.cursor()


def _get_connection_cursor_providers():
    conn = _get_connection(control.providercacheFile)
    return conn.cursor()


def _get_connection_cursor_search():
    conn = _get_connection(control.searchFile)
    return conn.cursor()


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _hash_function(function_instance, *args):
    return _get_function_name(function_instance) + _generate_md5(args)


def _get_function_name(function_instance):
    return re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', repr(function_instance))


def _generate_md5(*args):
    md5_hash = hashlib.md5()
    [md5_hash.update(str(arg)) for arg in args]
    return str(md5_hash.hexdigest())


def _is_cache_valid(cached_time, cache_timeout):
    now = int(time.time())
    diff = now - cached_time
    return (cache_timeout * 3600) > diff


def cache_version_check():
    if _find_cache_version():
        cache_clear(); cache_clear_meta(); cache_clear_providers(); cache_clear_search()
        control.infoDialog("Vorgang abgeschlossen", sound=True, icon='INFO')


def _find_cache_version():
    import os
    versionFile = os.path.join(control.dataPath, 'cache.v')
    try:
        with open(versionFile, 'rb') as fh:
            oldVersion = fh.read()
    except:
        oldVersion = '0'
    try:
        curVersion = control.addon('plugin.video.lastship').getAddonInfo('version')
        if oldVersion != curVersion:
            with open(versionFile, 'wb') as fh:
                fh.write(curVersion)
            return True
        else:
            return False
    except:
        return False
