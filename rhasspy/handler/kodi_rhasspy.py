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

map_to_ASCII = (
# UTF to ASCII
'', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',                   # 0x00
'', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',                   # 0x10
# ' ', '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/',  0x20
  ' ', '',  '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/',
# '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',   0x30
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
# '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',   0x40
  '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
# 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',  0x50
  'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',
# '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',   0x60
  '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
# 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', '',    0x70
  'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', '',
# '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�',   0x80
  '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
# '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�',   0x90
  '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
# ' ', '¡', '¢', '£', '¤', '¥', '¦', '§', '¨', '©', 'ª', '«', '¬', '­', '®', '¯',   0xa0
  ' ', '!', 'C/', 'PS', '$?', 'Y=', '|', 'SS', '"', '(c)', 'a', '<<', '!', '', '(r)', '-',
# '°', '±', '²', '³', '´', 'µ', '¶', '·', '¸', '¹', 'º', '»', '¼', '½', '¾', '¿',  0xb0
  'deg', '+-', '2', '3', '\'', 'u', 'P', '*', ',', '1', 'o', '>>', ' 1/4 ', ' 1/2 ', ' 3/4 ', '?',
# 'À', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'Æ',  'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì', 'Í', 'Î', 'Ï',  0xc0
  'A', 'A', 'A', 'A', 'A', 'A', 'AE', 'C', 'E', 'E', 'E', 'E', 'I', 'I', 'I', 'I',
# 'Ð', 'Ñ', 'Ò', 'Ó', 'Ô', 'Õ', 'Ö', '×', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý', 'Þ',  'ß',  0xd0
  'D', 'N', 'O', 'O', 'O', 'O', 'O', 'x', 'O', 'U', 'U', 'U', 'U', 'Y', 'Th', 'ss',
# 'à', 'á', 'â', 'ã', 'ä',  'å', 'æ',  'ç', 'è', 'é', 'ê', 'ë', 'ì', 'í', 'î', 'ï',  0xe0
  'a', 'a', 'a', 'a', 'ae', 'a', 'ae', 'c', 'e', 'e', 'e', 'e', 'i', 'i', 'i', 'i',
# 'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', '÷', 'ø', 'ù', 'ú', 'û', 'ü', 'ý', 'þ',  'ÿ',  0xf0
  'd', 'n', 'o', 'o', 'o', 'o', 'o', '/', 'o', 'u', 'u', 'u', 'u', 'y', 'th', 'y'
  )

map_to_SPEECH = (
# UTF to SPEECH
'', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',                   # 0x00
'', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',                   # 0x10
# ' ', '!', '"', '#', '$', '%', '&', ''', '(', ')', '*', '+', ',', '-', '.', '/',  0x20
  ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ',', ' ', '.', ' ',
# '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',  0x30
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ' ', ' ', ' ', ' ', ' ', '?',
# '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',  0x40
  ' ', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
# 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',  0x50
  'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', ' ', ' ', ' ', ' ', ' ',
# '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',  0x60
  ' ', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
# 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', DEL,  0x70
  'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', ' ', ' ', ' ', ' ', ' ',
# '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�',  0x80
  '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
# '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�', '�',  0x90
  '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
# ' ', '¡', '¢', '£', '¤', '¥', '¦', '§', '¨', '©', 'ª', '«', '¬', '­', '®', '¯',  0xa0
  '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
# '°', '±', '²', '³', '´', 'µ', '¶', '·', '¸', '¹', 'º', '»', '¼', '½', '¾', '¿',  0xb0
  '',  '',  '',  '',  '',  '',  '',  '',  '',  '',  '',  '',  '',  '',  '',  '',
# 'À', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'Æ', 'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì', 'Í', 'Î', 'Ï',  0xc0
  'A', 'A', 'A', 'A', 'AE','oo','AE','s', 'E', 'EE','E', 'E', 'I', 'I', 'I', 'I',
# 'Ð', 'Ñ', 'Ò', 'Ó', 'Ô', 'Õ', 'Ö', '×', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý', 'Þ',  'ß',  0xd0
  'D', 'NJ','O', 'O', 'O', 'O', 'eu',' ', 'eu',' ', 'eu','U', 'U', 'y', 'Th','ss',
# 'à', 'á', 'â', 'ã', 'ä', 'å', 'æ', 'ç', 'è', 'é', 'ê', 'ë', 'ì', 'í', 'î', 'ï',  0xe0
  'a', 'a', 'a', 'a', 'e', 'oo','ae','s', 'e', 'ee','e', 'e', 'i', 'i', 'i', 'i',
# 'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', '÷', 'ø', 'ù', 'ú', 'û', 'ü', 'ý', 'þ', 'ÿ',  0xf0
  'd', 'nj','o', 'o', 'o', 'o', 'eu',' ', 'eu','u', 'u', 'u', 'uu','y', 'th','y'
)

def get_replacement(char,mapping):

    if ord(char) > 0xff:
        # No data on characters > 255.
        return '?'
    try:
        return mapping[ord(char)]
    except IndexError: 
        log.error(f"Error replacing character {char} =0x{ord(char):02x}")

def decodeUTF8(string,mapping=map_to_ASCII):
    retval = []

    for char in string:
        retval.append(get_replacement(char,mapping))
    return ''.join(retval)


import datetime
import requests
import logging
import json
import re

from kodi import Kodi
from rhasspy import Rhasspy
log = logging.getLogger(__name__)

class Kodi_Rhasspy:

    def __init__(self, kodi, rhasspy):
        self.kodi = kodi
        self.rhasspy = rhasspy

    # 
    # ========================================================================
    # Methods to generate slots for Rhasspy
    # ========================================================================
    # Clean Slot_entry to match with filter
    def clean_all_filter(self,slot_entry):
        cleaned = slot_entry
        # skip everyting after ; or ,
        cleaned = re.sub('[;,].*','',cleaned)
        # skip leading numbers followed by - with spaces
        cleaned = re.sub('^[0-9 ]*-* *','',cleaned)
        # remove [ until the end : [] give problems in kaldi (rhasspy)
        cleaned = re.sub('\[.*','',cleaned)
        # remove ( until the end : () give problems in kaldi (rhasspy)
        cleaned = re.sub('\(.*','',cleaned) 
        # remove leading and trailing spaces
        cleaned = cleaned.strip()
        log.debug(f"clean_all_filter:<{slot_entry}> clean:<{cleaned}>")

        return cleaned
        
    # Clean slot_entry to match with speech
    def clean_all_speech(self,slot_entry):
        cleaned = self.clean_all_filter(slot_entry)
        cleaned = re.sub('&',' en ',cleaned)
        cleaned = decodeUTF8(cleaned, map_to_SPEECH)
        cleaned = re.sub('[^a-zA-Z0-9]',' ',cleaned)
        cleaned = re.sub('  *',' ',cleaned)

        cleaned = cleaned.strip()
        log.debug(f"clean_all_speech:<{slot_entry}> clean:<{cleaned}>")

        return cleaned

    # Clean Songtitle to match with filter
    def clean_songtitle_filter(self,songtitle):
        cleaned = songtitle.lower()
        # skip leading numbers followed by - with spaces
        cleaned = re.sub('^[0-9 ]*-* *','',cleaned)
        # remove leading composername followed by :
        cleaned = re.sub('^[a-z]*:','',cleaned)
        # keep only part before - or :
        cleaned = re.sub('[-:].*','',cleaned)
        # remove [ until the end
        cleaned = re.sub('\[.*','',cleaned)
        # remove ( until the end
        cleaned = re.sub('\(.*','',cleaned) # () give problems in kaldi (rhasspy)
        # remove Op. 23
        cleaned = re.sub('^[a-z]+[. ]*[0-9]+ *[0-9]*','',cleaned)
        cleaned = re.sub(' in (bes|cis|des|fis|ges|as|es|[a-g])* .*$',' ',cleaned)
        cleaned = re.sub('(bes|cis|des|fis|ges|as|es|[a-g]) (sharp|flat|moll|dur|majeur|mineur|major|minor|maj|min|klein|groot)$',' ',cleaned)
        cleaned = re.sub('([0-9])  *[0-9a-z]\.* .*$','\\1',cleaned)
        cleaned = re.sub('([0-9])  *[0-9.a-z]$','\\1',cleaned)
        cleaned = re.sub('[0-9]\..*','',cleaned) # . after number gives compile error??
        # very specific substitutions:
        cleaned = re.sub('.*contrapunctus.*','contrapunctus',cleaned)
        cleaned = re.sub('canto ostinato.*','canto ostinato',cleaned)
        cleaned = re.sub('goldberg variations.*','goldberg variations',cleaned)
        
        # remove leading and trailing spaces
        cleaned = cleaned.strip()
        log.debug(f"clean_songtitle_filter:<{songtitle}> clean:<{cleaned}>")

        return cleaned
        
    # Clean songtitle to match with speech
    def clean_songtitle_speech(self,songtitle):
        cleaned = self.clean_songtitle_filter(songtitle)
        # No.4 1 
        cleaned = re.sub('( no.\d) [1-9x].*','\\1',cleaned)
        cleaned = re.sub('op[. ]+\d*[-/0-9]*', '', cleaned)
        cleaned = re.sub('violin concerto.*','vioolconcert',cleaned)
        cleaned = re.sub('\.\.\.',',',cleaned)
        cleaned = re.sub('\[[^\]]*\]',' ',cleaned)
        cleaned = re.sub('["\'!]',' ',cleaned)
        cleaned = re.sub('[({].*[)}]',' ',cleaned)
        cleaned = re.sub(',',' ',cleaned)
        cleaned = re.sub('no\.','nummer ',cleaned)
        cleaned = re.sub('nr\.','nummer ',cleaned)
        cleaned = re.sub('&',' en ',cleaned)
        cleaned = decodeUTF8(cleaned, map_to_SPEECH)

        cleaned = re.sub('  *',' ',cleaned)

        cleaned = cleaned.strip()
        log.debug(f"clean_songtitle_speech:<{songtitle}> clean:<{cleaned}>")

        return cleaned

    '''
        Add to dict adds a speech to a list of entries
        If the speech already exists (we already have a filter defined)
        We check for:
        new is part of old: use new
        old is part of new: use old
        
    '''
    def add_to_dict(self,slot_entries,new_speech,new_filter):
        if new_speech in slot_entries:
            old_filter = slot_entries[new_speech]
            if new_filter in old_filter:
                my_filter = new_filter
            elif old_filter in new_filter:
                my_filter = old_filter
            else: # TODO Check the code
                my_filter = old_filter
                while not new_filter.startswith(old_filter):
                    old_filter = old_filter[:-1]
        else:
            my_filter = new_filter
            
        slot_entries[new_speech] = my_filter

    def dump(self,data):
        if type(data) is str:
            jdata = json.loads(data)
        elif type(data) is dict:
            jdata = data
        else:
            log.error(f"dump is called with wrong type: {type(data)}")
            return
        for slotname, slots in jdata.items():
            fslots = open(slotname, "w+")
            for line in slots:
                fslots.write(line+'\n')
            fslots.close()

    def save_slots(self,slots_dict,slotname):
        slots = []
        for speech,title in sorted(slots_dict.items()):
            if title.startswith(speech):
                slots.append(speech)
            else:
                slots.append(f"({speech}):({title})")
        slots_dict = { slotname :  slots }
        log.debug(f"Send to Rhasspy:<<<<{json.dumps(slots_dict)}>>>>")
        self.rhasspy.rhasspy_replace_slots(json.dumps(slots_dict))
        self.rhasspy.rhasspy_train()

    def create_slots_albums(self,albums):
        albumslots = {}
        
        for album in albums:
            filter_album = self.clean_all_filter(album["label"])
            speech_album = self.clean_all_speech(filter_album)
            if filter_album == "" or speech_album == "":
                continue
            self.add_to_dict(albumslots,speech_album,filter_album)

        self.save_slots(albumslots,"albums")

    def create_slots_songs(self,songs):
        songslots = {}
        for song in songs:
            filter_song = self.clean_songtitle_filter(song["label"])
            speech_song = self.clean_songtitle_speech(filter_song)
            if filter_song == "" or speech_song == "":
                continue
            self.add_to_dict(songslots,speech_song,filter_song)

        self.save_slots(songslots,"songs")

    def create_slots_composers(self,songs):
        composerslots = {}
        for song in songs:
            filter_composer = self.clean_all_filter(song["displaycomposer"])
            speech_composer = self.clean_all_speech(filter_composer)
            self.add_to_dict(composerslots,speech_composer,filter_composer)

        self.save_slots(composerslots,"composers")

    def create_slots_artists(self,albums):
        artistslots = {}
        for album in albums:
            for artist in album["artist"]:
                filter_artist = self.clean_all_filter(artist)
                speech_artist = self.clean_all_speech(filter_artist)
                self.add_to_dict(artistslots,speech_artist,filter_artist)

        self.save_slots(artistslots,"artists")


    def create_slots_genres(self,albums):
        genreslots = {}
        for album in albums:
            for genre in album["genre"]:
                filter_genre = self.clean_all_filter(genre)
                speech_genre = self.clean_all_speech(filter_genre)
                self.add_to_dict(genreslots,speech_genre,filter_genre)

        self.save_slots(genreslots,"genres")
  
    def create_slots_files(self):
        songs = self.kodi.get_songs(genre="Klassiek")
        if len(songs) > 0:
            self.create_slots_songs(songs)
            self.create_slots_composers(songs)
        albums = self.kodi.get_albums()
        if len(albums) > 0:
            self.create_slots_artists(albums)
            self.create_slots_albums(albums)
            self.create_slots_genres(albums)

if __name__ == '__main__':

    '''
    getallalbums = 
    {"jsonrpc":"2.0","method":"AudioLibrary.GetAlbums","params":{"limits": { "start" : 0, "end": 5000 },"properties":["artist","genre"],
    "sort":{"order":"ascending","method":"album"}},"id":"libAlbums"}
    getallsongs =
    {"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs","params": { "limits": { "start" : 0, "end": 50000 },"properties": ["displayartist", "displaycomposer"],
    "filter":{"field": "genre", "operator": "contains","value": "klassiek"}},
    "id": "libSongs"}
            # data = data + ',"sort": { "order": "ascending", "method": "title", "ignorearticle": true }'
            data = data + '
    '''
    logging.basicConfig(filename='kodi.log',
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-4.4s %(module)-14.14s - %(message)s',
                        datefmt='%Y%m%d %H:%M:%S')

    kodi_url = "http://192.168.0.5:8080"
    kodi = Kodi(kodi_url)

    rhasspy_url = "http://192.168.0.5:12101"
    rhasspy = Rhasspy(rhasspy_url)
    
    kodi_rhasspy = Kodi_Rhasspy(kodi,rhasspy)
    # #kodi.add_album_to_playlist("217")
    # kodi.pause_resume()
    import sys
    if len(sys.argv) > 3:
        matchtitle = sys.argv[3]
    else: matchtitle = ""
    if len(sys.argv) > 2:
        artist = sys.argv[2]
    else: artist = ""
    if len(sys.argv) > 1:
        composer = sys.argv[1]
    else:
        kodi_rhasspy.create_slots_files()
    
# End Of File
