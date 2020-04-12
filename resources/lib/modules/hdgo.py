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
import urlparse

from resources.lib.modules import dom_parser
from resources.lib.modules import client

def getPlaylistLinks(url):
    hdgoContent = client.request(url)
    playlistLink = dom_parser.parse_dom(hdgoContent, 'iframe')
    if len(playlistLink) > 0:
        playlistLink = playlistLink[0].attrs['src']
        playListContent = client.request('http:' + playlistLink)
        links = re.findall('\[(".*?)\]', playListContent, re.DOTALL)
        links = links[0].split(',')
        links = [i.replace('"', '').replace('\r\n','').replace('/?ref=hdgo.cc', '') for i in links]
        return [urlparse.urljoin('http://hdgo.cc', i) for i in links]
    return

def getStreams(url, sources, quality, skiplast=True, quali="HD"):
    if quality is not None:
        quali=quality
    if 'hdgo' in url:
        hdgostreams = getHDGOStreams(url)
        if hdgostreams is not None:
            if len(hdgostreams) > 1 and skiplast:
                hdgostreams.pop(0)
            quality = ["SD", "HD", "1080p", "2K", "4K"]
            for i, stream in enumerate(hdgostreams):
                sources.append({'source': 'hdgo.cc', 'quality': quality[i], 'language': 'de',
                                'url': stream + '|Referer=' + url, 'direct': True,
                                'debridonly': False})
    elif 'streamz' in url:
        streamzstream = getstreamzStreams(url)
        if streamzstream is not None:
            stream = client.request(streamzstream, output='geturl')
            sources.append({'source': 'streamz.cc', 'quality': quali, 'language': 'de',
                            'url': stream, 'direct': True,
                            'debridonly': False})
    elif 'vio' in url:
        Viotreams = getViotreams(url)
        if Viotreams is not None:
            if len(Viotreams) > 1 and skiplast:
                Viotreams.pop(0)
            quality = ["SD", "HD", "1080p", "2K", "4K"]
            for i, stream in enumerate(Viotreams):
                sources.append({'source': 'vio', 'quality': quality[i], 'language': 'de',
                                'url': stream + '|Referer=' + url, 'direct': True,
                                'debridonly': False})
    elif 'vivo.php' in url:
        vivostream = getvivo_php_Streams(url)
        if vivostream is not None:
            stream = client.request(vivostream, output='geturl')
            sources.append({'source': 'vivo', 'quality': quali, 'language': 'de',
                            'url': stream, 'direct': True,
                            'debridonly': False})
    return sources


def getHDGOStreams(url):
    try:
        request = client.request(url, referer=url)
        request = dom_parser.parse_dom(request, 'iframe')[0].attrs['src']
        request = client.request(urlparse.urljoin('http://', request), referer=url)
        request = re.findall("media:\s(\[.*?\])", request, re.DOTALL)[0]
        request = re.findall("'(.*?\')", request)
        return ["https:" + i.replace("'", "") for i in request if i[:2] == "//"]
    except:
        return None

def getViotreams(url):
    try:
        request = client.request(url, referer=url)
        request = re.findall(r'{url: \'(.*?)\'', request)
        return ["https:" + i.replace("'", "") for i in request if i[:2] == "//"]
    except:
        return None

def getstreamzStreams(url):
    try:
        request = client.request(url, referer=url)
        request = re.findall(r'{src: \'(.*?)\',type', request)[0]
        return request
    except:
        return None

def getvivo_php_Streams(url):
    try:
        request = client.request(url, referer=url)
        request = re.findall(r'<video\s*id="player"[^>]+data-stream="([^"]+)', request)
        return request[0].decode('base64')
    except:
        return None
