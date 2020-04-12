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

import socket
import hashlib
import hmac
import time
import urllib
import urllib2
import base64
import traceback
from BaseHTTPServer import BaseHTTPRequestHandler

from resources.lib.modules import pyaes

from resources.lib.modules import control

try:
    import json
except Exception:
    import simplejson as json
from binascii import hexlify

LAST_HTTP_ERROR_CODE = 0
LAST_HTTP_ERROR_DATA = ''


def updateStatus(type, data, code=None):
    obj = {'type': type, 'data': data, 'code': code}
    print 'Recaptcha2: %s' % json.dumps(obj).encode('utf-8')


DEBUGE = False


def printDBG(strDat):
    if DEBUGE:
        print("%s" % strDat)


def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")


def getPage(url, headers={}, post_data=None):
    printDBG('url [%s]' % url)
    customOpeners = []

    try:
        ctx = ssl._create_unverified_context()
        customOpeners.append(urllib2.HTTPSHandler(context=ctx))
    except Exception:
        pass

    sts = 0
    data = ''
    try:
        req = urllib2.Request(url)
        for key in headers:
            req.add_header(key, headers[key])

        printDBG("++++HEADERS START++++")
        printDBG(req.headers)
        printDBG("++++HEADERS END++++")

        opener = urllib2.build_opener(*customOpeners)
        response = opener.open(req)
        data = response.read()
        sts = response.getcode()
    except urllib2.HTTPError, e:
        global LAST_HTTP_ERROR_CODE
        global LAST_HTTP_ERROR_DATA
        LAST_HTTP_ERROR_CODE = e.code
        LAST_HTTP_ERROR_DATA = e.fp.read()
        sts = LAST_HTTP_ERROR_CODE
        data = LAST_HTTP_ERROR_DATA
        printExc()
    except Exception:
        printExc()
    return sts, data


class MYJDException(BaseException):
    pass


def PAD(s):
    BS = 16
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


def UNPAD(s):
    return s[0:-ord(s[-1])]


class Jddevice:
    def __init__(self, jd, device_dict):
        self.name = device_dict["name"]
        self.device_id = device_dict["id"]
        self.device_type = device_dict["type"]
        self.myjd = jd

    def action(self, path, params=(), http_action="POST"):
        action_url = self.__action_url()
        response = self.myjd.request_api(path, http_action, params, action_url)
        if response is None:
            return False
        return response['data']

    def __action_url(self):
        return "/t_" + self.myjd.get_session_token() + "_" + self.device_id


class Myjdapi:
    def __init__(self):
        self._request_id = int(time.time() * 1000)
        self._api_url = "http://api.jdownloader.org"
        self._app_key = "http://git.io/vmcsk"
        self._api_version = 1
        self._devices = None
        self._login_secret = None
        self._device_secret = None
        self._session_token = None
        self._regain_token = None
        self._server_encryption_token = None
        self._device_encryption_token = None
        self._connected = False

    def get_device_secret(self):
        return self._device_secret

    def get_session_token(self):
        return self._session_token

    def get_server_encryption_token(self):
        return self._server_encryption_token

    def get_device_encryption_token(self):
        return self._device_encryption_token

    def is_connected(self):
        return self._connected

    def set_app_key(self, app_key):
        self._app_key = app_key

    def __secret_create(self, email, password, domain):
        secret_hash = hashlib.sha256()
        secret_hash.update(email.lower().encode('utf-8') + password.encode('utf-8') + \
                           domain.lower().encode('utf-8'))
        return secret_hash.digest()

    def _update_encryption_tokens(self):
        if self._server_encryption_token is None:
            old_token = self._login_secret
        else:
            old_token = self._server_encryption_token
        new_token = hashlib.sha256()
        new_token.update(old_token + bytearray.fromhex(self._session_token))
        self._server_encryption_token = new_token.digest()
        new_token = hashlib.sha256()
        new_token.update(self._device_secret + bytearray.fromhex(self._session_token))
        self._device_encryption_token = new_token.digest()

    def _signature_create(self, key, data):
        signature = hmac.new(key, data.encode('utf-8'), hashlib.sha256)
        return signature.hexdigest()

    def _decrypt(self, secret_token, data):
        decryptor = self._getCryptor(secret_token)
        decoded = base64.b64decode(data)
        decrypted_data = ""
        for part in [decoded[i:i+16] for i in range(0, len(decoded), 16)]:
            decrypted_data += decryptor.decrypt(part)
        decrypted_data = UNPAD(decrypted_data)
        return decrypted_data

    def _encrypt(self, secret_token, data):
        data = PAD(data.encode('utf-8'))
        encryptor = self._getCryptor(secret_token)
        encrypted_data = ""
        for part in [data[i:i+16] for i in range(0, len(data), 16)]:
            encrypted_data += encryptor.encrypt(part)
        encrypted_data = base64.b64encode(encrypted_data)
        return encrypted_data.decode('utf-8')

    def _getCryptor(self, secret_token):
        init_vector = secret_token[:len(secret_token) // 2]
        key = secret_token[len(secret_token) // 2:]
        return pyaes.AESModeOfOperationCBC(key, iv=init_vector)

    def update_request_id(self):
        self._request_id = int(time.time())

    def connect(self, email, password):
        self._login_secret = self.__secret_create(email, password, "server")
        self._device_secret = self.__secret_create(email, password, "device")
        response = self.request_api("/my/connect", "GET", [("email", email), ("appkey", self._app_key)])
        self._connected = True
        self.update_request_id()
        self._session_token = response["sessiontoken"]
        self._regain_token = response["regaintoken"]
        self._update_encryption_tokens()

    def reconnect(self):
        response = self.request_api("/my/reconnect", "GET",
                                    [("sessiontoken", self._session_token), ("regaintoken", self._regain_token)])
        self.update_request_id()
        self._session_token = response["sessiontoken"]
        self._regain_token = response["regaintoken"]
        self._update_encryption_tokens()

    def disconnect(self):
        response = self.request_api("/my/disconnect", "GET", [("sessiontoken", self._session_token)])
        self.update_request_id()
        self._login_secret = None
        self._device_secret = None
        self._session_token = None
        self._regain_token = None
        self._server_encryption_token = None
        self._device_encryption_token = None
        self._devices = None
        self._connected = False

    def update_devices(self):
        response = self.request_api("/my/listdevices", "GET", [("sessiontoken", self._session_token)])
        self.update_request_id()
        self._devices = response["list"]

    def request_api(self, path, http_method="GET", params=None, action=None):
        data = None
        if not self.is_connected() and path != "/my/connect":
            raise (MYJDException("No connection established\n"))
        if http_method == "GET":
            query = [path + "?"]
            for param in params:
                if param[0] != "encryptedLoginSecret":
                    query += ["%s=%s" % (param[0], urllib.quote(param[1]))]
                else:
                    query += ["&%s=%s" % (param[0], param[1])]
            query += ["rid=" + str(self._request_id)]
            if self._server_encryption_token is None:
                query += ["signature=" + \
                          str(self._signature_create(self._login_secret, query[0] + "&".join(query[1:])))]
            else:
                query += ["signature=" + \
                          str(self._signature_create(self._server_encryption_token, query[0] + "&".join(query[1:])))]
            query = query[0] + "&".join(query[1:])
            encrypted_response_status_code, encrypted_response_text = getPage(self._api_url + query)
        else:
            params_request = []
            for param in params:
                if not isinstance(param, list):
                    # params_request+=[str(param).replace("'",'\"').replace("True","true").replace("False","false").replace('None',"null")]
                    params_request += [json.dumps(param)]
                else:
                    params_request += [param]
            params_request = {"apiVer": self._api_version, "url": path, "params": params_request,
                              "rid": self._request_id}
            data = json.dumps(params_request).replace('"null"', "null").replace("'null'", "null")
            encrypted_data = self._encrypt(self._device_encryption_token, data)
            if action is not None:
                request_url = self._api_url + action + path
            else:
                request_url = self._api_url + path
            encrypted_response_status_code, encrypted_response_text = getPage(request_url, headers={
                "Content-Type": "application/aesjson-jd; charset=utf-8"}, data=encrypted_data)
        if encrypted_response_status_code != 200:
            error_msg = json.loads(encrypted_response_text)
            msg = "\n\tSOURCE: " + error_msg["src"] + "\n\tTYPE: " + \
                  error_msg["type"] + "\n------\nREQUEST_URL: " + \
                  self._api_url + path
            if http_method == "GET":
                msg += query
            msg += "\n"
            if data is not None:
                msg += "DATA:\n" + data
            raise (MYJDException(msg))
        if action is None:
            if not self._server_encryption_token:
                response = self._decrypt(self._login_secret, encrypted_response_text)
            else:
                response = self._decrypt(self._server_encryption_token, encrypted_response_text)
        else:
            if params is not None:
                response = self._decrypt(self._device_encryption_token, encrypted_response_text)
            else:
                return {"data": ""}
        jsondata = json.loads(response.decode('utf-8'))
        if jsondata['rid'] != self._request_id:
            self.update_request_id()
            return None
        self.update_request_id()
        return jsondata


class MyjdRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        printDBG(format % args)

    def parse_request(self):
        idx = -1
        for i in range(0, len(self.raw_requestline)):
            if self.raw_requestline[i] in "GPH":
                idx = i
                self.raw_requestline = self.raw_requestline[idx:]
                break
        if idx == -1:
            raise Exception("Wrong request %s..." % self.raw_requestline[:256])
        return BaseHTTPRequestHandler.parse_request(self)

    def _set_headers(self, returnCode=200, addHeaders=[]):
        self.send_response(returnCode)
        self.send_header('Connection', 'close')
        self.send_header('Cache-Control', 'no-store, no-cache')
        self.send_header('Content-type', 'application/json')
        for header in addHeaders:
            self.send_header(header[0], header[1])
        self.end_headers()

    def do_GET(self):
        self._set_headers(404)

    def do_HEAD(self):
        self._set_headers(501)

    def do_POST(self):
        jd = self.server
        return_data = ''
        returnCode = 200

        printDBG("In post method \n" + str(self.path))
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))

        session_token = self.path.split('/t_', 1)[-1].split('_', 1)[0]
        new_token = hashlib.sha256()
        new_token.update(jd.get_device_secret() + bytearray.fromhex(session_token))
        encryption_token = new_token.digest()

        printDBG("SESSION TOKEN: %s" % session_token)
        data = jd._decrypt(encryption_token, self.data_string)

        printDBG("ENCRYPTED_DATA [%s]: %s" % (len(self.data_string), self.data_string))
        printDBG("DECRYPTED_DATA [%s]: %s" % (len(data), data))

        data = json.loads(data)

        if data['url'] == '/device/getDirectConnectionInfos':
            updateStatus('status', "Client connected")
            return_data = {"infos": [], "rebindProtectionDetected": False, "mode": "NONE"}
        elif data['url'] == '/update/isUpdateAvailable':
            return_data = False
        elif data['url'] == '/config/get':
            if data['params'][-1] == '"DirectConnectMode"':
                return_data = "NONE"
            elif data['params'][-1] == '"manuallocalport"':
                return_data = 3129
            else:
                returnCode = 404
                # sys.exit(-1)
        elif data['url'] == '/captcha/list':
            if jd.captcha_result == None:
                return_data = [{'hoster': 'LastShip - Recaptcha', 'created': jd.captcha_data['id'], 'explain': None,
                                'id': jd.captcha_data['id'], 'captchaCategory': 'recaptchav2', 'link': 1535005786381L,
                                'timeout': 600000, 'type': 'RecaptchaV2Challenge', 'remaining': 593028}]
            else:
                return_data = []
        elif data['url'] == '/events/subscribe':
            return_data = {"subscriptionid": int(time.time() * 1000), "subscribed": True, "subscriptions": None,
                           "exclusions": None, "maxPolltimeout": 25000, "maxKeepalive": 120000}
            jd.captcha_notified = False
        elif data['url'] == '/events/setsubscription':
            return_data = {'maxKeepalive': 120000, 'subscribed': True,
                           'subscriptions': ['^downloads', '^extraction', '^linkcrawler', '^dialogs', '^captchas',
                                             '^downloadwatchdog'], 'maxPolltimeout': 25000,
                           'subscriptionid': data['params'][0], 'exclusions': ['REFRESH_CONTENT']}
            jd.captcha_notified = False
        elif data['url'] == '/linkcrawler/isCrawling':
            return_data = False
        elif data['url'] == '/dialogs/list':
            return_data = []
        elif data['url'] == '/downloadsV2/getStopMarkedLink':
            return_data = None
        elif data['url'] == '/polling/poll':
            return_data = [{'eventName': 'jdState', 'eventData': {'data': 'IDLE'}}, {'eventName': 'aggregatedNumbers',
                                                                                     'eventData': {'data': {
                                                                                         'crawledPackageCount': 0,
                                                                                         'downloadSpeed': 0,
                                                                                         'crawledStatusUnknown': 0,
                                                                                         'crawledStatusOnline': 0,
                                                                                         'crawledLinksCount': 0,
                                                                                         'packageCount': 0,
                                                                                         'linksCount': 0,
                                                                                         'connections': 0, 'running': 0,
                                                                                         'eta': 0,
                                                                                         'crawledStatusOffline': 0,
                                                                                         'totalBytes': 0,
                                                                                         'totalCrawledBytes': 0,
                                                                                         'loadedBytes': 0}}}]
        elif data['url'] == '/events/listen':
            return_data = []
            if jd.captcha_result == None and jd.captcha_notified == False:
                return_data = [{'eventid': 'NEW', 'eventData': jd.captcha_data['id'], 'publisher': 'captchas'}]
                jd.captcha_notified = True
            elif jd.captcha_result != None:
                return_data = [{"eventid": "DONE", "eventData": jd.captcha_data['id'], "publisher": "captchas"}]
                jd.captcha_finished = True

        elif data['url'] == '/captcha/getCaptchaJob':
            if jd.captcha_result == None:
                return_data = {'hoster': 'LastShip - Recaptcha', 'created': jd.captcha_data['id'], 'explain': None,
                               'id': jd.captcha_data['id'], 'captchaCategory': 'recaptchav2', 'link': 1535005786381L,
                               'timeout': 600000, 'type': 'RecaptchaV2Challenge', 'remaining': 593028}
            else:
                return_data = None
        elif data['url'] == '/captcha/get':
            if jd.captcha_result == None:
                updateStatus('status', "Waiting for captcha solving")
                return_data = jd.captcha_data
            else:
                return_data = None
        elif data['url'] == '/accountsV2/getPremiumHosterUrl':
            return_data = None
        elif data['url'] == '/captcha/solve':
            updateStatus('status', "Captcha solved")
            return_data = True
            jd.captcha_result = json.loads(data['params'][1]).encode('utf-8')
            updateStatus('captcha_result', jd.captcha_result)
        elif data['url'] == '/captcha/skip':
            updateStatus('status', "Captcha skipped")
            return_data = True
            jd.captcha_result = 'SKIPPED'
            jd.captcha_finished = True
        elif data['url'] == '/downloadevents/setStatusEventInterval':
            return_data = True
        elif data['url'] == '/linkgrabberv2/queryPackages':
            return_data = []
        elif data['url'] == '/accountsV2/listAccounts':
            return_data = []
        elif data['url'] == '/downloadcontroller/getCurrentState':
            return_data = '"IDLE"'
        elif data['url'] == '/linkgrabberv2/queryLinks':
            return_data = []
        elif data['url'] == '/downloadsV2/getStopMark':
            return_data = -1
        elif data['url'] == '/captcha/keepAlive':
            return_data = 600000
        elif data['url'] == '/contentV2/getFavIcon':
            return_data = None
        else:
            returnCode = 404
            # sys.exit(-1)

        self._set_headers(returnCode)
        return_data = '''{"data" : %s, "rid" : %s}''' % (json.dumps(return_data), data['rid'])

        printDBG('RETURN DATA: %s' % return_data)
        self.wfile.write(jd._encrypt(encryption_token, return_data))
        return


class MyJDownloader:
    def __init__(self):
        self.AppKey = "LastShip"
        self.User = control.setting('MyJDownloader.user')
        self.Password = control.setting('MyJDownloader.pass')
        self.IsAlive = True
        self.MyjdRequestHandler = None

    def solve(self, url, siteKey):
        CAPTCHA_DATA = {'siteKey': siteKey, 'sameOrigin': True, 'siteUrl': url, 'contextUrl': url,
                        'boundToDomain': True, 'stoken': None, 'id': int(time.time() * 1000)}

        hash = hashlib.sha256()
        hash.update(self.User + self.AppKey)
        DEVICEID = hexlify(hash.digest()[:16])
        try:
            while self.IsAlive:
                updateStatus('status', "Connecting to server")

                jd = Myjdapi()
                jd.set_app_key(self.AppKey)
                jd.connect(self.User, self.Password)

                response = jd.request_api("/my/binddevice", "GET",
                                          [("sessiontoken", jd.get_session_token()), ("deviceID", DEVICEID), ("type", "jd"),
                                           ("name", self.AppKey)])
                printDBG(response)
                jd.update_request_id()

                jd.captcha_finished = False
                jd.captcha_result = None
                jd.captcha_notified = False
                jd.captcha_data = CAPTCHA_DATA

                try:
                    updateStatus('status', "Waiting for client connection")
                    while jd.captcha_finished == False and self.IsAlive:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect(('api.jdownloader.org', 80))  # 88.99.115.46
                        s.send("DEVICE%s" % jd.get_session_token())
                        self.MyjdRequestHandler = MyjdRequestHandler(s, (None, None), jd)
                        s.close()
                except Exception as e:
                    printExc(str(e))
                    continue

                updateStatus('captcha_result', jd.captcha_result)
                break
        except MYJDException as e:
            updateStatus('error', str(e), LAST_HTTP_ERROR_CODE)
            printExc()
        except Exception as e:
            updateStatus('error', e, LAST_HTTP_ERROR_CODE)
            printExc()
        return jd.captcha_result if jd else ""

    def setKill(self):
        self.IsAlive = False
