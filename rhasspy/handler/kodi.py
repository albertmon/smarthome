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
    def __init__(self, url):
        self.url = url+"/jsonrpc"

    def do_post(self, data):
        log.debug(f"Post data(url={self.url}:<{data}>")
        try:
            res = requests.post(self.url, data=data.encode("utf-8"),
                                headers={"Content-Type": "application/json"})
            if res.status_code != 200:
                log.info("do_post(Url:[%s]\nResult:%s, text:[%s]"
                         % (url, res.status_code, res.text))
        except ConnectionError:
            log.warning(f"ConnectionError for url [{url}]")
            return None

        log.debug("Post Result:"+res.text)
        return(res.json())

    def get_whats_playing(self):
        log.debug("get_whats_playing")
        data = '{"jsonrpc":"2.0","method":"Player.GetItem","params":'\
                + '{"properties":["album", "artist", "genre", "title"]'\
                + ', "playerid": 0},"id":"itemData"}'
        return self.do_post(data)

    def stop_play(self):
        data = '{"jsonrpc": "2.0", "method": "Player.Stop",'\
               + ' "params": { "playerid": 1 }, "id": 1}'
        self.do_post(data)

    def start_play(self):
        data = '{"jsonrpc":"2.0", "id":1,"method":"Player.Open",'\
               + '"params":{"item":{"playlistid":0}}}'
        self.do_post(data)

    def pause_resume(self):
        data = '{"jsonrpc": "2.0", "method": "Player.PlayPause",'\
               + ' "params": { "playerid": 0 }, "id": 1}'
        self.do_post(data)

    def next_track(self):
        data = '{"jsonrpc": "2.0", "method": "Player.GoTo",'\
               + ' "params": { "playerid": 0 , "to":"next"}, "id": 1}'
        self.do_post(data)

    def previous_track(self):
        data = '{"jsonrpc": "2.0", "method": "Player.GoTo",'\
               + ' "params": { "playerid": 0 , "to":"previous"}, "id": 1}'
        self.do_post(data)
        data = '{"jsonrpc": "2.0", "method": "Player.GoTo",'\
               + ' "params": { "playerid": 0 , "to":"previous"}, "id": 1}'
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

    def add_stream_to_playlist(self, stream_url):
        data = '{"jsonrpc":"2.0", "id":1,"method":"Playlist.Add","params":{'\
               + '"playlistid":0, "item":{"file":"'+stream_url+'"}}}'
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


    def get_songs(self, artist="", composer="", title="", selection="", genre=""):
        log.debug(f"get_songs artist={artist}, "\
            + f"composer={composer}, title={title}")
        data = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs",'\
                + '"params": { "limits": { "start" : 0, "end": 50000 },'\
                + '"properties": ["displayartist", "displaycomposer"],'\
                + '"filter":{"and":[ '
        comma = ""
        if artist != "":
            data = data + comma + '{"field": "artist", "operator": "contains",'\
                + '"value": "'+artist+'"}'
            comma = ","
        if composer != "":
            data = data + comma + '{"field": "artist", "operator": "contains",'\
                + '"value": "'+composer+'"}'
            comma = ","
        if title != "":
            data = data + comma + '{"field": "title", "operator": "contains",'\
                + '"value": "'+title+'"}'
            comma = ","
        if selection != "":
            for select in selection.split(","):
                data = data + comma + '{"field": "title", "operator": "contains",'\
                    + '"value": "'+select+'"}'
                comma = ","
        if genre != "":
            data = data + comma + '{"field": "genre", "operator": "contains",'\
                + '"value": "'+genre+'"}'
        data = data + ']}'
        # data = data + ',"sort": { "order": "ascending", "method": "title", "ignorearticle": true }'
        data = data + '},"id": "libSongs"}'

        res = self.do_post(data)
        log.debug(f"get_songs:Found:{res['result']['limits']['end']}")

        if "result" in res and "songs" in res["result"]:
            songs = res["result"]["songs"]
        else:
            songs = []

        return songs

    def play_stream(self, stream_url):
        log.debug(f"play_stream:stream_url:{stream_url}")
        self.stop_play()
        self.clear_playlist()
        self.add_stream_to_playlist(stream_url)
        self.start_play()
        # data = '{"jsonrpc":"2.0", "id":1,"method":"Player.Open",'\
            # + '"params":{"item" : {"file":"' + stream_url + '" }}}'
        # self.do_post(data)

    def play_albums(self, albums):
        log.debug(f"play_albums:albums:{albums}")
        self.stop_play()
        self.clear_playlist()
        for album in albums:
            log.debug(f"album={album}")
            self.add_album_to_playlist(album["albumid"])
        self.start_play()

    def play_songs(self, songs):
        log.debug(f"play_songs:songs:{songs}")
        self.stop_play()
        self.clear_playlist()
        for song in songs:
            log.debug(f"On playlist: {song['songid']},label={song['label']}" \
                + f"van {song['displaycomposer']}")
            self.add_song_to_playlist(song["songid"])
        self.start_play()

# End Of File
