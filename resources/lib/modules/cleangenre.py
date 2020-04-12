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


def lang(i, lang):

    if lang == 'de':
    	i = i.replace('Adventure', 'Abenteuer')
        i = i.replace('Action', 'Action')
        i = i.replace('Animation', 'Animation')
        i = i.replace('Anime', 'Anime')
        i = i.replace('Biography', 'Biographie')
        i = i.replace('Documentary', 'Dokumentation')
        i = i.replace('Drama', 'Drama')
        i = i.replace('Family', 'Familie')
        i = i.replace('Fantasy', 'Fantasy')
        i = i.replace('Game-Show', 'Game-Show')
        i = i.replace('History', 'Historie')
        i = i.replace('Horror', 'Horror')
        i = i.replace('Comedy', 'Komödie')
        i = i.replace('War', 'Kriegsfilm')
        i = i.replace('Crime', 'Krimi')
        i = i.replace('Romance', 'Lovestory')
        i = i.replace('Musical', 'Musical')
        i = i.replace('Music ', 'Musik')
        i = i.replace('Mystery', 'Mystery')
        i = i.replace('News', 'News')
        i = i.replace('Reality-TV', 'Reality-TV')
        i = i.replace('Science Fiction', 'Science-Fiction')
        i = i.replace('Sci-Fi', 'Science-Fiction')
        i = i.replace('Sport', 'Sport')
        i = i.replace('Superhero', 'Superhelden')
        i = i.replace('Talk-Show', 'Talk-Show')
        i = i.replace('Thriller', 'Thriller')
        i = i.replace('Western', 'Western')

    return i
