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
from kodi_rhasspy import Kodi_Rhasspy

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
            selection - Select track only if track-title contains selection
            genre - Select track only if genre matches
    KodiPauseResume - Pause or Resume playing
        Parameters: None
    KodiStop - Stop playing playlist
        Parameters: None
    KodiStart - Start playing playlist
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

    def play_albums(self):
        artist = self.intentjson.get_slot_value("artist")
        album = self.intentjson.get_slot_value("album")
        genre = self.intentjson.get_slot_value("genre")
        artist_raw = self.intentjson.get_raw_value("artist")
        album_raw = self.intentjson.get_raw_value("album")
        log.debug(f"play_albums:(artist={artist}, album={album}, genre={genre})")
        albums = self.kodi.get_albums(artist=artist, album=album, genre=genre)

        question = intentconfig.get_text(intentconfig.KodiText.AskPlayConfirmation).\
            format(TITLE=album_raw, ARTIST=artist_raw)
        if len(albums) == 0:
            log.debug("play_albums:no albums found")
            no_music_found = intentconfig.get_text(intentconfig.KodiText.SayNoMusicFound).\
                format(TITLE=album_raw, ARTIST=artist_raw)
            self.intentjson.set_speech(no_music_found)
        elif self.rhasspy.rhasspy_confirm(question ):
            confirmation = intentconfig.get_text(intentconfig.KodiText.SayPlayConfirmation).\
                format(TITLE=album_raw, ARTIST=artist_raw)
            self.intentjson.set_speech(confirmation)
            self.kodi.play_albums(albums)
        else:
            no_confirmation = intentconfig.get_text(intentconfig.KodiText.SayNoPlayConfirmation)
            self.intentjson.set_speech(no_confirmation)
            
    def play_songs(self):
        artist = self.intentjson.get_slot_value("artist")
        composer = self.intentjson.get_slot_value("composer")
        genre = self.intentjson.get_slot_value("genre")
        title = self.intentjson.get_slot_value("title")
        selection = self.intentjson.get_slot_value("selection")
        log.debug(f"play_songs:(artist={artist}, composer={composer}, title=={title},"\
            + f"selection={selection}, genre={genre})")
        songs = self.kodi.get_songs(artist, composer, title, selection, genre)

        if selection == "":
            selection = intentconfig.get_text(intentconfig.KodiText.Music) 
        my_title = selection if title == "" else self.intentjson.get_raw_value("title")
        my_artist = self.intentjson.get_raw_value("composer")\
                    if artist == "" else self.intentjson.get_raw_value("artist")
        question = intentconfig.get_text(intentconfig.KodiText.AskPlayConfirmation).\
            format(TITLE=my_title, ARTIST=my_artist)
        if len(songs) == 0:
            no_music_found = intentconfig.get_text(intentconfig.KodiText.SayNoMusicFound).\
                format(TITLE=my_title, ARTIST=my_artist)
            self.intentjson.set_speech(no_music_found)
        elif self.rhasspy.rhasspy_confirm(question):
            confirmation = intentconfig.get_text(intentconfig.KodiText.SayPlayConfirmation).\
                format(TITLE=my_title, ARTIST=my_artist)
            self.intentjson.set_speech(confirmation)
            self.kodi.play_songs(songs)
        else:
            no_confirmation = intentconfig.get_text(intentconfig.KodiText.SayNoPlayConfirmation)
            self.intentjson.set_speech(no_confirmation)

    def play_stream(self):
        url = self.intentjson.get_slot_value("url")
        self.kodi.play_stream(url)

    # =================================================================================

    def doKodiSongs(self):
        self.play_songs()

    def doKodiAlbums(self):
        self.play_albums()

    def doKodiStream(self):
        self.play_stream()

    def doKodiPauseResume(self):
        self.kodi.pause_resume()

    def doKodiStop(self):
        self.kodi.stop()

    def doKodiStart(self):
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
            answer = intentconfig.get_text(intentconfig.KodiText.WhatsPlaying_Response)
            self.intentjson.set_speech(answer.format(TITLE=title, ALBUM=album, ARTIST=artist))
        else:
            answer = intentconfig.get_text(intentconfig.KodiText.WhatsPlaying_Error)
            self.intentjson.set_speech(answer)

    def doKodiUpdateSlots(self):
        question = intentconfig.get_text(intentconfig.KodiText.AskUpdateSlotsConfirmation)
        if self.rhasspy.rhasspy_confirm(question):
            self.rhasspy.rhasspy_speak(
                intentconfig.get_text(intentconfig.Text.Please_Wait))
            kodi_rhasspy = Kodi_Rhasspy(self.kodi, self.rhasspy)
            res = kodi_rhasspy.create_slots_files()
            if res:
                confirmation = res
            else :
                confirmation = intentconfig.get_text(intentconfig.KodiText.SayUpdateSlotsConfirmation)
        else:
            confirmation = intentconfig.get_text(intentconfig.KodiText.SayNoUpdateSlotsConfirmation)

        self.intentjson.set_speech(confirmation)


# End of file