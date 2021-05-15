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

from kodi import Kodi
from rhasspy import Rhasspy
import intentconfig
import logging
log = logging.getLogger(__name__)

class IntentKodi:
    '''
    Class IntentKodi implements intents for the Kodi 
    All intents accept the parameter:
        speech (optional, default depending intent)
            - text to speak after executing the intent

    Implemented Intents are:
    KodiClassical - Play classical genre music depending on parameters
        Parameters (all optional):
            artist - Select track only if artist matches
            composer - Select track only if composer matches
            title - Select track only if track-title contains title
            selection - Select track only if track-title contains selection
    KodiAlbums - Play selected albums
        Parameters (all optional):artist="", album="", genre=""
            artist - Select album only if album-artists contain artist
            album - Select album only if album-title matches
            genre - Select album only if album-genres contains genre
    KodiSongs - Play selected songs/tracks
        Parameters (all optional):
            artist - Select track only if artist matches
            composer - Select track only if composer matches
            title - Select track only if track-title contains title
            genre - Select track only if genre matches
    KodiPauseResume - Pause or Resume playing
        Parameters: None
    KodiVolume - Set the volume to a percentage (0-100(
        Parameters:
            volume (required) - Volume level between 0 and 100 (percentage)
    KodiPrevious - Goto the previous song of the playlist
        Parameters: None
    KodiNext - Goto the next song of the playlist
        Parameters: None
    KodiWhatsPlaying - Speak the songname, akbumname and artist that is currently playing
        Parameters: None

(speel:) (pianomuziek:piano|vioolmuziek:viool|cellomuziek:cello|pianoconcert|vioolconcert|celloconcert|nocturne|toccata|fuga:fug|concert|suite|cantates:cantate|alles:){selection} van ($composers){composer} [door ($artists){artist}]
(speel:) [(de:)|(het:)] (eerste:1|tweede:2|derde:no3|vierde:4|vijfde:5|zesde:6|zevende:7|achtste:8|negende:9){selection} (piano concert|viool concert|cello concert|brandenburger concert|symphonie){title} [van ($composers){composer}]
Speel (symphonie, [(nummer:)(1..9)]){selection}  [van ($composers){composer}]
Speel [de|het] ($titles){title}   [van ($composers){composer}]
    '''
    def __init__(self, intentjson):
        self.intentjson = intentjson
        kodi_url = intentconfig.get_url("Kodi")
        self.kodi = Kodi(kodi_url)
        rhasspy_url = intentconfig.get_url("Rhasspy")
        self.rhasspy = Rhasspy(rhasspy_url)

    def kodiplay_albums(self, albums):
        log.debug(f"kodiplay_albums:albums:{albums}")
        self.kodi.clear_playlist()
        for album in albums:
            log.debug(f"album={album}")

            if len(albums) == 1:
                intentjson.set_speech(f"Ik ga het album {album['label']}"\
                    + f"van {album['artist']} afspelen")

            log.debug("Put on playlist album {album}")
            self.kodi.add_album_to_playlist(album["albumid"])
        self.kodi.restart_play()

    def kodiplay_songs(self, songs):
        log.debug(f"kodiplay_songs:gotSongs:{songs}")
        self.kodi.clear_playlist()
        for song in songs:
            log.debug(f"On playlist: {song['songid']},label={song['label']}" \
                + f"van {song['displaycomposer']}")
            self.kodi.add_song_to_playlist(song["songid"])
        self.kodi.restart_play()

    def play_albums(self, artist="", album="", genre=""):
        log.debug(f"play_albums:(artist={artist}, album={album}, genre={genre})")
        # albums = get_albums(artist, album)
        albums = self.kodi.get_albums(artist=artist, album=album, genre=genre)

        if artist is "":
            artisttext = ""
        else :
            artisttext = f"van {artist}"

        if album is "":
            albumtext = "albums"
        else :
            albumtext = f"het album {album}"

        if genre is not None and len(genre) >= 3:
            genretekst = f"in het genre {genre}"
        else:
            genretekst = ""

        confirmtext = f"moet ik {albumtext} {artist} {genretekst} afspelen ?"
        if len(albums) == 0:
            log.debug("play_albums:geen album gevonden")
            if artist == "":
                artist = "een wilekeurige artiest"
            self.intentjson.set_speech("ik kan geen album "+album+" van "+artist+" vinden"+genretekst)
        elif self.rhasspy.rhasspy_confirm(confirmtext):
            self.intentjson.set_speech(f"ik ga {str(len(albums))} afspelen {genretekst}")
            self.kodiplay_albums(albums)
        else:
            self.intentjson.set_speech("okee dan niet")
            
    def play_songs(self, artist="", composer="", title="", selection="", genre=""):
        log.debug(f"play_songs:(artist={artist}, composer={composer}, title=={title},"\
            + f"selection={selection}, genre={genre})")
        songs = self.kodi.get_songs(artist, composer, title, selection, genre)

        if len(songs) == 0:
            log.debug("play_songs:geen muziek gevonden")
            self.intentjson.set_speech(f"ik kan geen muziek {title} vinden")
        elif self.rhasspy.rhasspy_confirm(f"moet ik muziek {title} afspelen ?"):
            self.intentjson.set_speech(f"ik ga de muziek {title} afspelen")
            self.kodiplay_songs(songs)
        else:
            self.intentjson.set_speech("okee dan niet")

    # =================================================================================

    def doKodiClassical(self):
        log.debug(f"doKodiClassical")
        title = self.intentjson.get_slot_value("title")
        selection = self.intentjson.get_slot_value("selection")
        artist = self.intentjson.get_slot_value("artist")
        composer = self.intentjson.get_slot_value("composer")
        log.debug(f"play_songs(artist={artist}, composer={composer}, title={title}, selection={selection}")
        self.play_songs(artist=artist, composer=composer, title=title, selection=selection, genre="Klassiek")

    def doKodiSongs(self):
        artist = self.intentjson.get_slot_value("artist")
        composer = self.intentjson.get_slot_value("composer")
        genre = self.intentjson.get_slot_value("genre")
        title = self.intentjson.get_slot_value("title")
        self.play_songs(artist=artist, composer=composer, title=title, genre=genre)

    def doKodiAlbums(self):
        artist = self.intentjson.get_slot_value("artist")
        album = self.intentjson.get_slot_value("album")
        genre = self.intentjson.get_slot_value("genre")
        self.play_albums(artist=artist, album=album, genre=genre)

    def doKodiPauseResume(self):
        self.kodi.pause_resume()

    def doKodiVolume(self):
        volume = self.intentjson.get_slot_value("volume")
        self.kodi.volume(volume)

    def doKodiPrevious(self):
        self.kodi.previous_track()

    def doKodiNext(self):
        self.kodi.next_track()

    def doKodiWhatsPlaying(self):
        answer = self.kodi.get_whats_playing()
        log.debug(str(answer))
        if 'result' in answer and 'item' in answer['result']:
            item = answer['result']['item']
            album = item["album"]
            artist = item["artist"]
            title = item["title"]
            # genre = item["genre"]
            self.intentjson.set_speech(f"Dit is het nummer, {title},"\
                + f"van het album, {album}, van, {artist}")
        else:
            self.intentjson.set_speech("Ik weet het niet, sorry")


