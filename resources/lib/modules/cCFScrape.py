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

import re, sys, urllib, urllib2
from time import sleep
from urlparse import urlparse
import ast
import operator as op

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def parseJSString(s):
    offset = 1 if s[0] == '+' else 0
    val = s.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0')[offset:]

    val = val.replace('(+0', '(0').replace('(+1', '(1')

    val = re.findall(r'\((?:\d|\+|\-)*\)', val)

    val = ''.join([str(eval_expr(i)) for i in val])
    return int(val)

def eval_expr(expr):
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

class cCFScrape:
    def resolve(self, url, cookie_jar, user_agent):
        Domain = re.sub(r'https*:\/\/([^/]+)(\/*.*)', '\\1', url)
        headers = {'User-agent': user_agent,
                   'Referer': url, 'Host': Domain,
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                   'Accept-Encoding': 'gzip, deflate',
                   'Connection': 'keep-alive',
                   'Upgrade-Insecure-Requests': '1',
                   'Content-Type': 'text/html; charset=utf-8'}

        try:
            cookie_jar.load(ignore_discard=True)
        except Exception as e:
            print (e)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        request = urllib2.Request(url)
        for key in headers:
            request.add_header(key, headers[key])

        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e

        if response.code != 503:
            return response

        body = response.read()
        cookie_jar.extract_cookies(response, request)
        cCFScrape.__checkCookie(cookie_jar)
        parsed_url = urlparse(url)
        submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, parsed_url.netloc)
        params = {}

        try:
            params["jschl_vc"] = re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)
            params["pass"] = re.search(r'name="pass" value="(.+?)"', body).group(1)
            params["s"] = re.search(r'name="s"\svalue="(?P<s_value>[^"]+)', body).group(1)
            js = self._extract_js(body, parsed_url.netloc)
        except:
            return None

        params["jschl_answer"] = js
        sParameters = urllib.urlencode(params, True)
        request = urllib2.Request("%s?%s" % (submit_url, sParameters))
        for key in headers:
            request.add_header(key, headers[key])
        sleep(5)

        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e
        return response

    @staticmethod
    def __checkCookie(cookieJar):
        for entry in cookieJar:
            if entry.expires > sys.maxint:
                entry.expires = sys.maxint

    @staticmethod
    def _extract_js(body, domain):
        init = re.findall('setTimeout\(function\(\){\s*var.*?.*:(.*?)}', body)[-1]
        builder = re.findall(r"challenge-form\'\);\s*(.*)a.v", body)[0]
        try:
            challenge_element = re.findall(r'id="cf.*?>(.*?)</', body)[0]
        except:
            challenge_element = None

        if '/' in init:
            init = init.split('/')
            decryptVal = parseJSString(init[0]) / float(parseJSString(init[1]))
        else:
            decryptVal = parseJSString(init)
        lines = builder.split(';')
        char_code_at_sep = '"("+p+")")}'

        for line in lines:
            if len(line) > 0 and '=' in line:
                sections = line.split('=')
                if len(sections) < 3:
                    if '/' in sections[1]:
                        subsecs = sections[1].split('/')
                        val_1 = parseJSString(subsecs[0])
                        if char_code_at_sep in subsecs[1]:
                            subsubsecs = re.findall(r"^(.*?)(.)\(function", subsecs[1])[0]
                            operand_1 = parseJSString(subsubsecs[0] + ')')
                            operand_2 = ord(domain[parseJSString(
                                subsecs[1][subsecs[1].find(char_code_at_sep) + len(char_code_at_sep):-2])])
                            val_2 = '%.16f%s%.16f' % (float(operand_1), subsubsecs[1], float(operand_2))
                            val_2 = eval_expr(val_2)
                        else:
                            val_2 = parseJSString(subsecs[1])
                        line_val = val_1 / float(val_2)
                    elif len(sections) > 2 and 'atob' in sections[2]:
                        expr = re.findall((r"id=\"%s.*?>(.*?)</" % re.findall(r"k = '(.*?)'", body)[0]), body)[0]
                        if '/' in expr:
                            expr_parts = expr.split('/')
                            val_1 = parseJSString(expr_parts[0])
                            val_2 = parseJSString(expr_parts[1])
                            line_val = val_1 / float(val_2)
                        else:
                            line_val = parseJSString(expr)
                    else:
                        if 'function' in sections[1]:
                            continue
                        line_val = parseJSString(sections[1])

                elif 'Element' in sections[2]:
                    subsecs = challenge_element.split('/')
                    val_1 = parseJSString(subsecs[0])
                    if char_code_at_sep in subsecs[1]:
                        subsubsecs = re.findall(r"^(.*?)(.)\(function", subsecs[1])[0]
                        operand_1 = parseJSString(subsubsecs[0] + ')')
                        operand_2 = ord(domain[parseJSString(
                            subsecs[1][subsecs[1].find(char_code_at_sep) + len(char_code_at_sep):-2])])
                        val_2 = '%.16f%s%.16f' % (float(operand_1), subsubsecs[1], float(operand_2))
                        val_2 = eval_expr(val_2)
                    else:
                        val_2 = parseJSString(subsecs[1])
                    line_val = val_1 / float(val_2)

                decryptVal = '%.16f%s%.16f' % (float(decryptVal), sections[0][-1], float(line_val))
                decryptVal = eval_expr(decryptVal)

        if '+ t.length' in body:
            decryptVal += len(domain)

        return float('%.10f' % decryptVal)
