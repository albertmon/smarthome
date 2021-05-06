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

import datetime
import requests
import logging
import re
log = logging.getLogger(__name__)

class Kodi:
    def __init__(self, url, path=""):
        self.url = url
        self.path = path

    def do_post(self, data):
        log.debug("Post data:"+data)
        try:
            res = requests.post(self.url, data=data,
                                headers={"Content-Type": "application/json"})
            if res.status_code != 200:
                log.info("do_post(Url:[%s]\nResult:%s, text:[%s]"
                         % (url, res.status_code, res.text))
        except ConnectionError:
            log.warning("ConnectionError for url [%s]" % (url))
            return None

        log.debug("Post Result:"+res.text)
        return(res.json())

    def get_whats_playing(self):
        log.debug("get_whats_playing")
        data = '{"jsonrpc":"2.0","method":"Player.GetItem","params":'\
                + '{"properties":["album", "artist", "genre", "title"]'\
                + ', "playerid": 0},"id":"itemData"}'
        return self.do_post(data)

    def restart_play(self):
        data = '{"jsonrpc": "2.0", "method": "Player.Stop",'\
               + ' "params": { "playerid": 1 }, "id": 1}'
        self.do_post(data)
        data = '{"jsonrpc":"2.0", "id":1,"method":"Player.Open",'\
               + '"params":{"item":{"playlistid":0}}}'
        self.do_post(data)

    def next_track(self):
        data = '{"jsonrpc": "2.0", "method": "Player.GoTo",'\
               + ' "params": { "playerid": 0 , "to":"next"}, "id": 1}'
        self.do_post(data)

    def previous_track(self):
        data = '{"jsonrpc": "2.0", "method": "Player.GoTo",'\
               + ' "params": { "playerid": 0 , "to":"previous"}, "id": 1}'
        self.do_post(data)

    def pause_resume(self):
        data = '{"jsonrpc": "2.0", "method": "Player.PlayPause",'\
               + ' "params": { "playerid": 0 }, "id": 1}'
        self.do_post(data)

    def volume(self, volume):
        data = '{"jsonrpc":"2.0", "method":"Application.SetVolume",'\
               + '"id":1,"params":{"volume":'+str(volume)+'}}'
        self.do_post(data)

    def clear_playlist(self):
        data = '{"jsonrpc":"2.0", "id":1,"method":"Playlist.Clear",'\
               + '"params":{"playlistid":0}}'
        self.do_post(data)

    def add_album_to_playlist(self, albumid):
        data = '{"jsonrpc":"2.0", "id":1,"method":"Playlist.Add","params":{'\
               + '"playlistid":0, "item":{"albumid":'+str(albumid)+'}}}'
        self.do_post(data)

    def add_song_to_playlist(self, songid):
        data = '{"jsonrpc":"2.0", "id":1,"method":"Playlist.Add","params":{'\
               + '"playlistid":0, "item":{"songid":'+str(songid)+'}}}'
        self.do_post(data)

    def get_albums(self,artist="", album="", genre=""):
        log.debug("get_albums")

        data = '{"jsonrpc":"2.0","method":"AudioLibrary.GetAlbums"'\
                + ',"params":{"properties":["artist","genre"]'
        if artist != "" or album != "" or genre != "":
            data = data + ',"filter":{"and":[{"field":"artist", "operator":'\
                + '"contains", "value":"'+artist+'"}'\
                + ',{"field":"album", "operator":'\
                + '"contains", "value":"'+album+'"}'\
                + ',{"field": "genre", "operator":'\
                + '"contains","value": "'+genre+'"}]}'
        data = data + ',"sort":{"order":"ascending","method":"album"}}'\
                + ',"id":"libAlbums"}'
        res = self.do_post(data)
        if "result" in res and "albums" in res["result"]:
            albums = res["result"]["albums"]
        else:
            albums = []
        return albums


    def get_tracks_klassiek(self, artist="", composer="", matchtitle=""):
        log.debug(f"get_tracks_klassiek artist={artist}, "\
            + f"composer={composer}, matchtitle={matchtitle}")
        data = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs",'\
                + '"params": { "limits": { "start" : 0, "end": 50000 },'\
                + '"properties": ["displayartist", "displaycomposer"],'\
                + '"filter":{"and":[ '\
                + '{"field": "genre", "operator": "contains","value": "klassiek"}'
        if artist != "":
            data = data + ',{"field": "artist", "operator": "contains",'\
                + '"value": "'+artist+'"}'
        if composer != "":
            data = data + ',{"field": "artist", "operator": "contains",'\
                + '"value": "'+composer+'"}'
        if matchtitle != "":
            data = data + ',{"field": "title", "operator": "contains",'\
                + '"value": "'+matchtitle+'"}'
        data = data + ']}'
        # data = data + ',"sort": { "order": "ascending", "method": "title", "ignorearticle": true }'
        data = data + '},"id": "libSongs"}'

        res = self.do_post(data)
        log.debug(f"get_tracks_klassiek:Found:{res['result']['limits']['end']}")

        if "result" in res and "songs" in res["result"]:
            tracks = res["result"]["songs"]
        else:
            tracks = []

        # if matchtitle != "":
            # print(f"Voor matching:"+str(tracks["result"])+"\n================================\n")
            # matched_tracks = []
            # searches = matchtitle.lower().split()
            # print(str(searches))
            # for track in tracks["result"]["songs"]:
                # matched = True
                # for match in searches:
                    # print(f"Test:{track['label']}<- match ->{match}:"+str(track["label"].lower().find(match)))
                    # if track["label"].lower().find(match) < 0 :
                        # matched = False
                        # break
                        
                # if matched:
                    # matched_tracks.append(track)
                    # print("Matched track:"+str(track))
            # tracks["result"]["songs"] = matched_tracks
        log.debug(f"Na matchtitle ({matchtitle}):"+str(tracks)+"\n========================\n")
        return tracks

    def add_tracks_to_playlist(self, artist, composer, matchtitle):
        tracks = self.get_tracks_klassiek(artist, composer, matchtitle)

        data = '{"jsonrpc":"2.0","id":1,"method":"Playlist.Add","params":{"playlistid":0,'\
               + '"item":'
        # "item":[{"songid":1839}, {"songid":1840}, {"songid":1841}, {"songid":1842}, {"songid":1878} ]}
        separator = '['
        for track in tracks:
            data = data + separator + '{"songid":' + str(track["songid"]) + '}'
            separator = ','
        data = data + ']}}'
        log.debug(f"Data:{data}")
        return self.do_post(data)

    # 
    # ========================================================================
    # Methods to generate slots-files for Rhasspy
    # ========================================================================
    # Clean Albumtitle to match with filter
    def clean_albumtitle_filter(self,albumtitle):
        cleaned = albumtitle.lower()
        # skip leading numbers followed by - with spaces
        cleaned = re.sub('^[0-9 ]*-* *','',cleaned)
        # remove [ until the end : [] give problems in kaldi (rhasspy)
        cleaned = re.sub('\[.*','',cleaned)
        # remove ( until the end : () give problems in kaldi (rhasspy)
        cleaned = re.sub('\(.*','',cleaned) 
        # remove leading and trailing spaces
        cleaned = cleaned.strip()

        return cleaned
        
    # Clean albumtitle to match with speech
    def clean_albumtitle_speech(self,albumtitle):
        cleaned = self.clean_albumtitle_filter(albumtitle)
        # No.4 1 
        cleaned = re.sub('[^a-z0-9]',' ',cleaned)
        cleaned = re.sub('  *',' ',cleaned)

        cleaned = cleaned.strip()

        return cleaned

    # Clean Tracktitle to match with filter
    def clean_tracktitle_filter(self,tracktitle):
        cleaned = tracktitle.lower()
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
        cleaned = re.sub(' in (bes|cis|des|fis|ges|as|es|[a-g])* *(sharp|flat|moll|dur)* *(majeur|mineur|major|minor|maj|min|klein|groot)* *$',' ',cleaned)
        cleaned = re.sub('(bes|cis|des|fis|ges|as|es|[a-g]) (sharp|flat|moll|dur|majeur|mineur|major|minor|maj|min|klein|groot)$',' ',cleaned)
        cleaned = re.sub('([0-9])  *[0-9a-z]\.* .*$','\\1',cleaned)
        cleaned = re.sub('([0-9])  *[0-9.a-z]$','\\1',cleaned)
        cleaned = re.sub('[0-9]\..*','',cleaned) # . after number gives compile error
        cleaned = re.sub('.*contrapunctus.*','contrapunctus',cleaned)
        cleaned = re.sub('canto ostinato.*','canto ostinato',cleaned)
        cleaned = re.sub('goldberg variations.*','goldberg variations',cleaned)
        
        # remove leading and trailing spaces
        cleaned = cleaned.strip()

        return cleaned
        
    # Clean tracktitle to match with speech
    def clean_tracktitle_speech(self,tracktitle):
        cleaned = self.clean_tracktitle_filter(tracktitle)
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
        cleaned = re.sub('  *',' ',cleaned)

        cleaned = cleaned.strip()

        return cleaned

    def add_to_dict(self,slot_entries,new_speech,new_filter):
        if new_speech in slot_entries:
            old_filter = slot_entries[new_speech]
            if new_filter in old_filter:
                my_filter = new_filter
            elif old_filter in new_filter:
                my_filter = old_filter
            else:
                my_filter = old_filter
                while not new_filter.startswith(old_filter):
                    old_filter = old_filter[:-1]
        else:
            my_filter = new_filter
            
        slot_entries[new_speech] = my_filter

    def save_slots(self,slots_dict,filename):
        fslots = open(self.path+filename, "w+")
        for speech,title in sorted(slots_dict.items()):
            if title.startswith(speech):
                slotstring = speech
            else:
                slotstring = (f"({speech}):({title})")
            fslots.write(slotstring+'\n')
        fslots.close()

    def create_slots_albums(self,albums):
        albumslots = {}
        
        for album in albums:
            speech_title = self.clean_albumtitle_speech(album["label"])
            filter_title = self.clean_albumtitle_filter(album["label"])
            if filter_title == "" or speech_title == "":
                continue
            self.add_to_dict(albumslots,speech_title,filter_title)

        self.save_slots(albumslots,"albums")

    def create_slots_tracks(self,tracks):
        trackslots = {}
        for track in tracks:
            speech_title = self.clean_tracktitle_speech(track["label"])
            filter_title = self.clean_tracktitle_filter(track["label"])
            if filter_title == "" or speech_title == "":
                continue
            self.add_to_dict(trackslots,speech_title,filter_title)
       
        self.save_slots(trackslots,"tracks")

    def create_slots_composers(self,tracks):
        composerset = set()
        for track in tracks:
            composer = re.sub('[;,].*','',track["displaycomposer"])
            composerset.add(composer.lower())
            
        fcomposers = open(self.path+"composers", "w+")
        for composer in sorted(composerset):
            fcomposers.write(composer+'\n')
        fcomposers.close()


    def create_slots_artists(self,albums):
        artistset = set()
        
        for album in albums:
            for artist in album["artist"]:
                artistset.add(artist.lower())

        fartists = open(self.path+"artists", "w+")
        for artist in sorted(artistset):
            fartists.write(artist+'\n')
        fartists.close()


    def create_slots_genres(self,albums):
        genreset = set()
        for album in albums:
            for genre in album["genre"]:
                genreset.add(genre.lower())

        fgenres = open(self.path+"genres", "w+")
        for genre in sorted(genreset):
            fgenres.write(genre+'\n')
        fgenres.close()
  
    def create_slots_files(self):
        tracks = self.get_tracks_klassiek("","","")
        if len(tracks) > 0:
            self.create_slots_tracks(tracks)
            self.create_slots_composers(tracks)
        albums = self.get_albums()
        if len(albums) > 0:
            self.create_slots_artists(albums)
            self.create_slots_albums(albums)
            self.create_slots_genres(albums)
        
if __name__ == '__main__':

    '''
    getallalbums = 
    {"jsonrpc":"2.0","method":"AudioLibrary.GetAlbums","params":{"limits": { "start" : 0, "end": 5000 },"properties":["artist","genre"],
    "sort":{"order":"ascending","method":"album"}},"id":"libAlbums"}
    getalltracks =
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

    kodi_url = "http://192.168.0.5:8080/jsonrpc"

    kodi = Kodi(kodi_url)
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
        kodi.create_slots_files()
    
# End Of File
