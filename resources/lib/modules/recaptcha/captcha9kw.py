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

import xbmc
import json

from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import utils


class captcha9KW:
    def __init__(self):
        self.ApiKey = control.setting('Captcha9kw.ApiKey')
        self.SolveType = control.setting('Captcha9kw.SolveType')
        self.IsAlive = True
        self.time = int(control.setting('Recaptcha2.TimeOut'))

    def solve(self, url, siteKey):

        if self.ApiKey == "":
            control.infoDialog("Kein Captcha9KW API-Key eingetragen!")
            return

        token = ''
        post = {
            'apikey': self.ApiKey,
            'action': 'usercaptchaupload',
            'interactive': '1',
            'json': '1',
            'file-upload-01': siteKey,
            'oldsource': 'recaptchav2',
            'pageurl': url,
            'maxtimeout': self.time
        }

        if self.SolveType == 'true':
            post['selfsolve'] = '1'


        try:
            token = ''
            data = client.request('https://www.9kw.eu/index.cgi', post=post)
            if data:
                data = utils.byteify(json.loads(data))
                if 'captchaid' in data:
                    captchaid = data['captchaid']
                    tries = 0
                    while tries < self.time and self.IsAlive:
                        tries += 1
                        xbmc.sleep(1000)

                        data = client.request('https://www.9kw.eu/index.cgi?apikey=' + self.ApiKey + '&action=usercaptchacorrectdata&json=1&id=' + captchaid)
                        if data:
                            print str(data)
                            data = utils.byteify(json.loads(data))
                            token = data['answer']
                            if token is not None and token != '':
                                break

        except Exception as e:
            print '9kw Error: ' + str(e)
        return token

    def setKill(self):
        self.IsAlive = False
