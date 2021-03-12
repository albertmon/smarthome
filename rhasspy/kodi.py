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
log = logging.getLogger(__name__)

class Kodi:
    def __init__(self, url):
        self.url = url

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

    def get_all_albums(self):
        log.debug("get_all_albums")
        data = '{"jsonrpc":"2.0","method":"AudioLibrary.GetAlbums"'\
                + ',"params":{"properties":["artist","genre"]'\
                + ',"sort":{"order":"ascending","method":"album"}}'\
                + ',"id":"libAlba"}'
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

if __name__ == '__main__':
    logging.basicConfig(filename='kodi.log',
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)-4.4s %(module)-14.14s - %(message)s',
                        datefmt='%Y%m%d %H:%M:%S')

    kodi_url = "http://192.168.0.5:8080/jsonrpc"

    kodi = Kodi(kodi_url)
    #kodi.add_album_to_playlist("217")
    kodi.pause_resume()

