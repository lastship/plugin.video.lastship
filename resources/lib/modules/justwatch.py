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

'''
import justwatch

base = 'https://apis.justwatch.com/content/titles/de_DE/popular'
header = justwatch.get_head()
payload = justwatch.get_payload("naruto", ["show"], ["flatrate","ads","free"], ["nfx","wbx","ntz"])

req = requests.post(base, headers=header, json=payload)

Providers
Full    Short   ID
Amazon  amz

'''

from random import choice
#import cleantitle
from resources.lib.modules import cleantitle


def get_head(ref='https://www.justwatch.com'):
    ''' Takes a Referer and give´s back a
    full Justwatch Header with random Agent'''

    site = 'https://www.justwatch.com'

    agents = ("Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 6.0.1; SGP771 Build/32.2.A.0.253; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
            "Mozilla/5.0 (CrKey armv7l 1.5.16041) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; XBOX_ONE_ED) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
            "Mozilla/5.0 (Linux; Android 5.1; AFTS Build/LMY47O) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/41.99900.2250.0242 Safari/537.36",
            "Mozilla/5.0 (PlayStation 4 3.11) AppleWebKit/537.73 (KHTML, like Gecko)",
            "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727)",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3",
            "Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 8_1_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B440 Safari/600.1.4",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.63 Safari/537.36",
            "Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0")

    header = {"User-Agent": choice(agents),
            "Origin": site,
            "Referer": ref}

    return header


def get_payload(title, c_types, m_types, providers):
    ''' All Inputs MUST be Lists
        c-types ["movie"] OR ["show"]
        m-types ["flatrate","ads","free"]
        Providers ["nfx","wbx","ntz", ...] '''

    title = cleantitle.get(title)

    payload = {"languages":"de",
                "content_types": c_types,
                "providers": providers,
                "monetization_types": m_types,
                "page":1,
                "page_size":10,
                "query": title}

    return payload


def get_offer(data, year, title, localtitle, provider_id):
    ''' Go´s through offers and make´s Compare
        Return´s [offer, hit['id'], hit['full_path']]'''

    site = 'https://www.justwatch.com'

    title = cleantitle.get(title)
    localtitle = cleantitle.get(localtitle)
    # Loop through hits
    for hit in data:
        # Compare year and title
        if (int(hit['original_release_year']) == int(year)
                and localtitle == cleantitle.get(hit['title'])
                or localtitle == cleantitle.get(hit['original_title'])
                or title == cleantitle.get(hit['original_title'])
                or title == cleantitle.get(hit['title'])
                ):

                for offer in hit['offers']:
                    if (int(offer['provider_id']) == int(provider_id)
                            and offer['presentation_type'] == 'hd'):
                        return offer, hit['id'], site + str(hit['full_path'])
                        break

                    elif (int(offer['provider_id']) == int(provider_id)
                            and offer['presentation_type'] == 'sd'):
                        return offer, hit['id'], site + str(hit['full_path'])
                        break

                    elif int(offer['provider_id']) == int(provider_id):
                        return offer, hit['id'], site + str(hit['full_path'])
                        break


