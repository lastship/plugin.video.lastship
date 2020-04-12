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

import threading

import xbmc
import xbmcgui
from resources.lib.modules import control

from resources.lib.modules.recaptcha import myJDownloader
from resources.lib.modules.recaptcha import TwoCaptcha
from resources.lib.modules.recaptcha import captcha9kw


class recaptchaApp:
    def __init__(self):
        self.siteKey = ""
        self.url = ""
        self.result = ""

    def callRecap(self, recap):
        self.result = recap.solve(self.url, self.siteKey)
        control.execute('Dialog.Close(yesnoDialog)')

    def getSolutionWithDialog(self, url, siteKey, infotext):
        time = int(control.setting('Recaptcha2.TimeOut'))
        self.url = url
        self.siteKey = siteKey
        line1 = "Folge den Anweisungen in MyJDownloader!"
        if "0" == control.setting('Recaptcha2.Mode'):
            recap = myJDownloader.MyJDownloader()
            t = threading.Thread(target=self.callRecap, args=(recap,))
        elif "1" == control.setting('Recaptcha2.Mode'):
            recap = TwoCaptcha.TwoCaptcha()
            t = threading.Thread(target=self.callRecap, args=(recap,))
            line1 = "Captcha wurde an 2Captcha gesendet!"
        else:
            recap = captcha9kw.captcha9KW()
            t = threading.Thread(target=self.callRecap, args=(recap,))
            line1 = "Captcha wurde an Captcha9KW gesendet!"

        t.start()

        dialogResult = xbmcgui.Dialog().yesno(heading="Captcha | " + infotext, line1=line1, line2="Zeit: %s s" % time, nolabel="Abbrechen", yeslabel="Mehr Info", autoclose=time*1000)
        if dialogResult:
            xbmc.log("YesNo-Dialog closed with true", xbmc.LOGDEBUG)
        else:
            xbmc.log("YesNo-Dialog closed with false", xbmc.LOGDEBUG)
        if self.result != "":
            #we have gotten a result! :)
            return self.result.strip()
        elif dialogResult:
            #more info
            win = PopupRecapInfoWindow()
            win.doModal()
            win.show()
            while control.condVisibility('Window.IsActive(PopupRecapInfoWindow)'):
                xbmc.log("Info-Dialog still open...", xbmc.LOGDEBUG)
                xbmc.sleep(1000)
            return ""
        else:
            #timeout or cancel
            recap.setKill()
            xbmc.sleep(1000)
            t.join()
            return ""

class PopupRecapInfoWindow(xbmcgui.WindowDialog):
    def __init__(self):
        self.width = 1280
        self.height = 720

        self.dialogWidth = 550
        self.dialogHeight = 220
        self.centerX = (self.width - self.dialogWidth)/2
        self.centerY = (self.height - self.dialogHeight)/2

        PLUGIN_ID = 'plugin.video.lastship'
        MEDIA_URL = 'special://home/addons/{0}/resources/media/'.format(PLUGIN_ID)
        back = MEDIA_URL + 'background.jpg'
        qr = MEDIA_URL + 'qr.png'

        self.addControl(xbmcgui.ControlImage(x=self.centerX, y=self.centerY, width=self.dialogWidth, height=self.dialogHeight, filename=back))
        self.addControl(xbmcgui.ControlImage(x=self.centerX+10, y=self.centerY+10, width=200, height=200, filename=qr))
        self.addControl(xbmcgui.ControlLabel(x=self.centerX+220, y=self.newLinePos(), width=600, height=25, font='font14', label="QR-Code Scannen oder"))
        self.addControl(xbmcgui.ControlLabel(x=self.centerX+220, y=self.newLinePos()+10, width=600, height=25, font='font14', label="Webseite besuchen:"))
        self.addControl(xbmcgui.ControlLabel(x=self.centerX+220, y=self.newLinePos()+20, width=600, height=25, font='font14', label="https://bit.ly/2NGvFHT"))
        self.okButton = xbmcgui.ControlButton(x=self.centerX+250, y=self.centerY + self.dialogHeight-125, height=60, width=300, font='font14', label="OK", alignment=2, textOffsetY=15, focusedColor="0xFF000000", textColor="0xFF00BBFF")
        self.addControl(self.okButton)
        self.setFocus(self.okButton)

    def onControl(self, controlID):
        # Toggle mode(tuning/setting)
        if controlID == self.okButton:
            self.close()

    def onAction(self, action):
        if action == xbmcgui.ACTION_NAV_BACK:
            self.close()

    def newLinePos(self):
        self.centerY = self.centerY + 25
        return self.centerY
