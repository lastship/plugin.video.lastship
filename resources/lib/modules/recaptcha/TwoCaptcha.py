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


class TwoCaptcha:
    def __init__(self):
        self.ApiKey = control.setting('2Captcha.ApiKey')
        self.IsAlive = True
        self.time = int(control.setting('Recaptcha2.TimeOut'))

    def solve(self, url, siteKey):
        if self.ApiKey == "":
            control.infoDialog("Kein 2Captcha API-Key eingetragen!")
            return

        token = ''
        post = {
            'key': self.ApiKey,
            'method': 'userrecaptcha',
            'invisible': '1',
            'json': '1',
            'googlekey': siteKey,
            'pageurl': url
        }

        try:
            token = ''
            data = client.request('https://2captcha.com/in.php', post=post)
            if data:
                data = utils.byteify(json.loads(data))
                if 'status' in data and data['status'] == 1:
                    captchaid = data['request']
                    tries = 0
                    while tries < self.time and self.IsAlive:
                        tries += 1
                        xbmc.sleep(1000)

                        data = client.request('https://2captcha.com/res.php?key=' + self.ApiKey + '&action=get&json=1&id=' + captchaid)
                        if data:
                            print str(data)
                            data = utils.byteify(json.loads(data))
                            if data['status'] == 1 and data['request'] != '':
                                token = data['request']
                                break

        except Exception as e:
            print '2Captcha Error: ' + str(e)
        return token

    def setKill(self):
        self.IsAlive = False
