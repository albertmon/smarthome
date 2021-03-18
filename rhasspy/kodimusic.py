#!/usr/bin/env python
'''
Copyright 2021 - Albert Montijn (montijnalbert@gmail.com)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
   
   ---------------------------------------------------------------------------
   Programming is the result of learning from others and making errors.
   A good programmer often follows the tips and tricks of better programmers.
   The solution of a problem seldom leads to new or original code.
   So any resemblance to already existing code is purely coincidental
'''

import os
import json
import random
import datetime
import re
import subprocess
from kodi import Kodi

import logging
log = logging.getLogger(__name__)

class Music:
    def __init__(self, kodi, musicfile):
        self.kodi = kodi
        self.musicfile = musicfile

    def get_albuminfo(self, albumid):
        with open(self.musicfile, "r") as music_file:
            music_json = json.load(music_file)
        log.debug("get_albuminfo: albumid=%s, musicfile=%s"
                 % (albumid, self.musicfile))

        album_info_list = []
        for album_info in music_json["albums"]:
            if album_info["id"] == str(albumid):
                log.debug("album_info (%s) matcht (%s)" % ( str(album_info) , str(albumid)))
                album_info_list.append(album_info)
                break
        log.debug("Gevonden: %s" % str(album_info_list))
        return album_info_list

    def search_albuminfo(self, artist="", album="", genre=""):
        artist_name = artist.lower()
        album_name = album.lower()

        with open(self.musicfile, "r") as music_file:
            music_json = json.load(music_file)
        log.debug("kodiGetAlbums:artist=[%s], album=[%s], genre=[%s], musicfile=[%s]"
                 % (artist_name, album_name, genre, self.musicfile))

        album_info_list = [album_info for album_info in music_json["albums"]
                           if (artist_name == ""
                               or album_info["artistsearch"] == artist_name)
                           and (album_name == ""
                                or album_info["albumsearch"] == album_name)
                           and (genre == ""
                                or genre in album_info["genre"])
                           ]
        log.debug("Gevonden: %s" % str(album_info_list))
        return album_info_list

    def cleanup(self, original, remove_az09=False):
        cleaned = original.lower()
        # remove special characters
        cleaned = re.sub('[^0-9a-z ]+', ' ', cleaned)
        # extra cleanup for album titles, not artists
        if remove_az09:
            # remove combinations of digits + letters
            cleaned = re.sub('[0-9]+[a-z]+', '', cleaned)
            # remove combinations of letters + digits
            cleaned = re.sub('[a-z]+[0-9]+', '', cleaned)
            # remove leading digits and spaces
            cleaned = re.sub('^[0-9 ]+', '', cleaned)
        # remove consecutive spaces to 1 space
        cleaned = re.sub(' +', ' ', cleaned)
        # remove trailing spaces
        cleaned = re.sub(' +$', '', cleaned)
        return cleaned

    def json_cleanup(self, original):
        cleaned = re.sub('[\'"]', '_', original)
        return cleaned

    def refresh_album_info(self, path):
        answer = self.kodi.get_all_albums()
        log.debug(str(answer))
        if answer['result'] is not None:
            albums = answer['result']['albums']
        else:
            albums = {}

        genres = set()
        artists = set()
        albumnames = set()

        fmusic = open(self.musicfile, "w+")
        # separator is added before datastring and changed to ',' in the loop
        separator = '{"albums":['

        for album in albums:
            artist = ""
            artistsearch = ""
            for a in album["artist"]:
                artist = artist + a + " "
                artistsearch = artistsearch + a + ","
            artistsearch = self.cleanup(artist)
            artists.add(artistsearch)

            genre = ""
            for g in album["genre"]:
                genre = genre + g + " "
            genres.add(genre)

            albumlabel = self.json_cleanup(album["label"])
            albumsearch = self.cleanup(albumlabel, remove_az09=True)
            albumnames.add(albumsearch)
            line = '%s{"id":"%s","artist":"%s","album":"%s",'\
                         % (separator, album["albumid"], artist, albumlabel)\
                         + '"genre":"%s","artistsearch":"%s","albumsearch":"%s"}\n'\
                         % (genre, artistsearch, albumsearch)
            log.debug(line)
            fmusic.write(line)
            separator = ','

        fmusic.write(']}')
        fmusic.close()

        NL = '\n'
        fgenres = open(path+"genres", "w+")
        for genre in sorted(genres):
            fgenres.write(genre+NL)
        fgenres.close()

        fartists = open(path+"artists", "w+")
        for artist in sorted(artists):
            fartists.write(artist+NL)
        fartists.close()

        falbums = open(path+"albums", "w+")
        for album in sorted(albumnames):
            falbums.write(album+NL)
        falbums.close()


if __name__ == '__main__':
    logging.basicConfig(filename='kodimusic.log',
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-4.4s:%(module)-10.10s - %(message)s',
                        datefmt='%Y%m%d %H:%M:%S')
    kodi_url = "http://192.168.0.5:8080/jsonrpc"
    os.chdir("/profiles/nl/handler")
    kodi = Kodi(kodi_url)
    music = Music(kodi, "music")

    music.refresh_album_info("")  # create files in current directory

    # test
    albumlist = music.get_albuminfo("4")
    log.info("album[4]:"+str(albumlist))
    print("album[4]:"+str(albumlist))
    print("------------------------------------------")
    albumlist = music.search_albuminfo("pink floyd", "echoes")
    log.info("pink floyd, echoes:"+str(albumlist))
    print("pink floyd, echoes:"+str(albumlist))
    print("------------------------------------------")
    albumlist = music.search_albuminfo("pink floyd", "")
    log.info("only pink floyd:"+str(albumlist))
    print("only pink floyd:"+str(albumlist))
    print("------------------------------------------")
    albumlist = music.search_albuminfo("", "echoes")
    log.info("only echoes:"+str(albumlist))
    print("only echoes:"+str(albumlist))
    print("------------------------------------------")
    albumlist = music.search_albuminfo(genre="Jaz")
    log.info("Jazz:"+str(albumlist))
    print("Jazz:"+str(albumlist))
    print("------------------------------------------")

