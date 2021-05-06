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

#import kodi

import logging
log = logging.getLogger(__name__)

class IntentKodi:
    def __init__(self, intentjson, kodi, rhasspy):
        self.intentjson = intentjson
        self.kodi = kodi
        self.rhasspy = rhasspy

    def kodiplay_albums(self, albums):
        log.debug("kodiplay_albums:gotAlbums:%s" % (str(albums)))
        self.kodi.clear_playlist()
        log.debug("albums[0]=%s" % (str(albums[0])))
        for album in albums:
            log.debug("album=%s" % (str(album)))

            if len(albums) == 1:
                intentjson.set_speech("Ik ga het album %s van %s afspelen"
                       % (album["label"], str(album["artist"])))

            log.debug("Ik ga het album %s (%s) van %s op playlist zetten" %
                      (album["albumid"], album["label"], str(album["artist"])))
            self.kodi.add_album_to_playlist(album["albumid"])
        self.kodi.restart_play()

    def kodiplay_songs(self, songs):
        log.debug("kodiplay_songs:gotSongs:%s" % (str(songs)))
        self.kodi.clear_playlist()
        log.debug("songs[0]=%s" % (str(songs[0])))
        for song in songs:
            log.debug("song=%s" % (str(song)))

            log.debug(f"Ik ga song %s (%s) van %s op playlist zetten" %
                      (song["songid"], song["label"], song["displaycomposer"]))
            self.kodi.add_song_to_playlist(song["songid"])
        self.kodi.restart_play()


    def play_artist_album(self, artist="", album="", genre=""):
        log.debug("play_artist_album:(artist=%s, album=%s, genre=%s)"
                  % (artist, album, genre))
        # albums = get_albums(artist, album)
        albums = self.kodi.get_albums(artist=artist, album=album, genre=genre)

        if artist is "":
            artisttext = ""
        else :
            artisttext = f" van {artist}"

        if album is "":
            albumtext = " albums"
        else :
            albumtext = f" het album {album}"

        if genre is not None and len(genre) >= 3:
            genretekst = " in het genre " + genre
        else:
            genretekst = ""

        confirmtext = f"moet ik {albumtext}{artist}{genretekst} afspelen ?"
        if len(albums) == 0:
            log.debug("play_artist_album:geen album gevonden")
            if artist == "":
                artist = "een wilekeurige artiest"
            self.intentjson.set_speech("ik kan geen album "+album+" van "+artist+" vinden"+genretekst)
        elif self.rhasspy.rhasspy_confirm(confirmtext):
            self.intentjson.set_speech(f"ik ga {str(len(albums))} afspelen {genretekst}")
            self.kodiplay_albums(albums)
        else:
            self.intentjson.set_speech("okee dan niet")

    def play_tracks_klassiek(self, artist="", composer="", matchtitle=""):
        log.debug("play_tracks_klassiek:(artist=%s, composer=%s, matchtitle==%s)"
                  % (artist, composer, matchtitle))
        tracks = self.kodi.get_tracks_klassiek(artist, composer, matchtitle)

        if len(tracks) == 0:
            log.debug("play_tracks_klassiek:geen tracks gevonden")
            self.intentjson.set_speech("ik kan geen treks "+matchtitle+" vinden")
        elif self.rhasspy.rhasspy_confirm(f"moet ik muziek {matchtitle} afspelen ?"):
            self.intentjson.set_speech(f"ik ga de treks {matchtitle} afspelen")
            self.kodiplay_songs(tracks)
        else:
            self.intentjson.set_speech("okee dan niet")

    # def play_by_id(albumid):
        # albums = kodi.get_albuminfo(albumid)
        # if len(albums) == 0:
            # log.debug("kodiplay:geen album gevonden")
            # intentjson.set_speech("ik kan geen album nummer "+str(albumid)+" vinden")
        # else:
            # kodiplay(albums)

    # =================================================================================

    def doMuziekKlassiek(self):
        '''
        [MuziekKlassiek]
        (speel:) (pianomuziek:piano|vioolmuziek:viool|cellomuziek:cello|pianoconcert|vioolconcert|celloconcert|nocturne|toccata|fuga|concert|suite){match} [van ($composers){composer}] [door ($artists){artist}]
        (speel:)  [(de:)|(het:)] (eerste:1|tweede:2|derde:no3|vierde:4|vijfde:5|zesde:6|zevende:7|achtste:8|negende:9){selectienum} (piano concert|viool concert|cello concert|brandenburger concert|symphonie){selectie} [van ($composers){composer}]
        Speel (symphonie [nummer:no.  (1..9) ] ){match}  [van ($composers){composer}]
        Speel [de|het] ($tracks){track}   [van ($composers){composer}]
        '''
        log.debug(f"doMuziekKlassiek")
        track = self.intentjson.get_slot_value("track")
        log.debug(f"doMuziekKlassiek: track=>{track}<")
        selectie = self.intentjson.get_slot_value("selectie")
        log.debug(f"doMuziekKlassiek: selectie=>{selectie}<")
        artist = self.intentjson.get_slot_value("artist")
        composer = self.intentjson.get_slot_value("composer")
        log.debug(f"play_tracks_klassiek(artist={artist}, composer={composer}, matchtitle={track}{selectie}")
        self.play_tracks_klassiek(artist=artist, composer=composer, matchtitle=track+selectie)

    def doMuziekVanArtist(self):
        artist = self.intentjson.get_slot_value("artist")
        self.play_artist_album(artist=artist)


    def doMuziekVanAlbum(self):
        album = self.intentjson.get_slot_value("album")
        self.play_artist_album(album=album)


    def doMuziekVanAlbumArtist(self):
        artist = self.intentjson.get_slot_value("artist")
        album = self.intentjson.get_slot_value("album")
        self.play_artist_album(artist=artist, album=album)


    def doMuziekVanGenre(self):
        genre = self.intentjson.get_slot_value("genre")
        play_artist_album(genre=genre)


    # def doMuziekAlbumid():
        # # speel album nummer  (0..500){albumid}
        # albumid = self.intentjson.get_slot_value("albumid")
        # play_by_id(albumid)


    def doMuziekAlbumlijstVanArtist(self):
        # welke albums (zijn er|hebben we) van ($artists){artist}
        self.intentjson.set_speech("Ik kan nog geen lijst van albums geven")


    def doMuziekPauseResume(self):
        self.kodi.pause_resume()


    def doMuziekVolume(self):
        volume = self.intentjson.get_slot_value("volume")
        self.kodi.volume(volume)


    def doMuziekPrevious(self):
        self.kodi.previous_track()


    def doMuziekNext(self):
        self.kodi.next_track()

    def doMuziekWhatsPlaying(self):
        answer = self.kodi.get_whats_playing()
        log.debug(str(answer))
        if 'result' in answer and 'item' in answer['result']:
            item = answer['result']['item']
            album = item["album"]
            artist = item["artist"]
            title = item["title"]
            # genre = item["genre"]
            self.intentjson.set_speech("Dit is het nummer, %s, van het album, %s, van, %s"
                   % (title, album, artist))
        else:
            self.intentjson.set_speech("Ik weet het niet, sorry")


