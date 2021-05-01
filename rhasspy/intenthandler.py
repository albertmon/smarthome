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

import sys
import json
import random
import datetime
import requests
import subprocess
import kodi

import logging
log = logging.getLogger(__name__)

PATH = "/profiles/nl/handler/"

duckduckgo_url = 'https://api.duckduckgo.com/?'
domticz_url = "http://192.168.0.3:8080/json.htm?"
kodi_url = "http://192.168.0.5:8080/jsonrpc"
rhasspy_url = "http://192.168.0.3:12101/api/"

temperatuur_idx = "19"
wind_idx = "20"
electricity_idx = "6"

windnaam = {"N": "noord",
            "NNE": "noord noord oost",
            "NE": "noord oost",
            "ENE": "oost noord oost",
            "E": "oost",
            "ESE": "oost zuid oost",
            "SE": "zuid oost",
            "SSE": "zuid zuid oost",
            "S": "zuid",
            "SSW": "zuid zuid west",
            "SW": "zuid west",
            "WSW": "west zuid west",
            "W": "west",
            "WNW": "west noord west",
            "NW": "noord west",
            "NNW": "noord noord west"}


def speech(text):
    global jsonevent
    log.debug("speech:"+text)
    jsonevent["speech"] = {"text": text}
    log.debug(str(jsonevent["speech"]))


def get_slot_value(slot_name,default=""):
    if slot_name in jsonevent["slots"]:
        return jsonevent["slots"][slot_name]
    return default

def get_raw_value_for(entity_name):
    for entity in jsonevent["entities"]:
        if entity["entity"] == entity_name:
            return entity["raw_value"]
    return ""

def get_speech(text_to_speak):
    is_var = False
    new_speech = ""
    for text in text_to_speak.split('.'):
       if is_var:
           new_speech = new_speech + get_raw_value_for(text)
       else:
           new_speech = new_speech + text
       is_var = not is_var
    return new_speech

# =============================================================================
# Conversations/Confirmation
def do_post_rhasspy(url,data=""):
    log.debug("Post data to rhasspy_url:"+data)
    try:
        res = requests.post(url, data=data)
        if res.status_code != 200:
            log.info("do_post(Url:[%s]\nResult:%s, text:[%s]"
                     % (url, res.status_code, res.text))
    except ConnectionError:
        log.warning("ConnectionError for url [%s]" % (url))
        return None

    # log.debug("Post Result:"+res.text)
    return(res)


def rhasspy_speak(question):
    do_post_rhasspy(rhasspy_url+"text-to-speech",question)

def rhasspy_listen_for_intent():
    res = do_post_rhasspy(rhasspy_url+"listen-for-command?nohass=true")
    return res.json()


def rhasspy_confirm(question):
    rhasspy_speak(question)
    res = rhasspy_listen_for_intent()
    log.debug(f"Reply={str(res)}")
    return("intent" in res and res["intent"]["name"] == "Confirm")


def get_domoticz(command):
    url = domticz_url+command
    log.debug("Url:"+url)
    try:
        res = requests.get(url)
        if res.status_code != 200:
            log.info("Url:["+url+"]\nResult:" + res.status_code
                     + ", text:"+res.text)
            return None
    except ConnectionError:
        timestamp = datetime.datetime.now().strftime("%Y%m%d %H:%M")
        log.warning("ConnectionError for url "+url+" at "+timestamp)
        return None

    log.debug(str(res.text))
    res_json = json.loads(res.text)

    if "result" in res_json:
        return(res_json["result"][0])

    return(None)

def domo_get_info(idx):
      # "Level": 80,
      # "LevelInt": 12,
      # "MaxDimLevel": 15,
      # "Name": "Tafellicht",

    command = "type=devices&rid=%d" % (idx)
    res_json = get_domoticz(command)
    log.debug("Domotcz result: "+str(res_json))
    if "MaxDimLevel" in res_json:
        maxDimLevel = int(res_json["MaxDimLevel"])
    else:
        maxDimLevel = 100
    if "Name" in res_json:
        name = res_json["Name"]
    else:
        name = "unknown"
    return (maxDimLevel, name)

def get_duckduckgo(artist="", album="", genre=""):
    search = ""
    if genre != "":
        search = "genre "+genre
    else:
        if album != "":
            search = "album %s %s" % (album, artist)
        else:
            search = artist

    params = { 'q': search, 'kad': 'nl_NL', 'kl': 'nl-nl', 'format': 'json' }

    log.debug("duckduckgo("+search+")")
    try:
        res = requests.get(duckduckgo_url, params=params)
        if res.status_code != 200:
            log.info("Url:["+duckduckgo_url+"]\nResult:" + res.status_code
                     + ", text:"+res.text)
    except ConnectionError:
        log.error("ConnectionError for url "+duckduckgo_url)

    log.debug(str(res.text))
    res_json = json.loads(res.text)

    if res_json["AbstractText"] is None or res_json["AbstractText"] == "":
        return("Geen informatie over %s gevonden" % (search))
    else:
        return(res_json["AbstractText"])


# ================  Intent handlers =================================


def domoDimmer(idx, state, level=-1):
    log.debug("domoDimmer(%d, %s, %d)" % (idx, state, level))
    if level >= 0:
        (maxDimLevel,name) = domo_get_info(idx)
        log.debug("(maxDimLevel=%d,name=%s)"\
                  % (maxDimLevel,name))
        level = int((level * maxDimLevel)/100 + 0.5)
        switchcmd = "Set Level&level=%d" % (level)
    else:
        switchcmd = state
    command = "type=command&param=switchlight&idx=%d&switchcmd=%s"\
        % (idx, switchcmd)
    get_domoticz(command)


def domoSwitch(idx, state):
    command = "type=command&param=switchlight&idx=%s&switchcmd=%s"\
        % (idx, state)
    get_domoticz(command)


def domoScene(idx):
    command = "type=command&param=switchscene&idx=%s&switchcmd=On" % (idx)
    get_domoticz(command)


def kodiplay_albums(albums):
    log.debug("kodiplay_albums:gotAlbums:%s" % (str(albums)))
    kodi.clear_playlist()
    log.debug("albums[0]=%s" % (str(albums[0])))
    for album in albums:
        log.debug("album=%s" % (str(album)))

        if len(albums) == 1:
            speech("Ik ga het album %s van %s afspelen"
                   % (album["label"], str(album["artist"])))

        log.debug("Ik ga het album %s (%s) van %s op playlist zetten" %
                  (album["albumid"], album["label"], str(album["artist"])))
        kodi.add_album_to_playlist(album["albumid"])
    kodi.restart_play()

def kodiplay_songs(songs):
    log.debug("kodiplay_songs:gotSongs:%s" % (str(songs)))
    kodi.clear_playlist()
    log.debug("songs[0]=%s" % (str(songs[0])))
    for song in songs:
        log.debug("song=%s" % (str(song)))

        log.debug(f"Ik ga song %s (%s) van %s op playlist zetten" %
                  (song["songid"], song["label"], song["displaycomposer"]))
        kodi.add_song_to_playlist(song["songid"])
    kodi.restart_play()


def play_artist_album(artist="", album="", genre=""):
    log.debug("play_artist_album:(artist=%s, album=%s, genre=%s)"
              % (artist, album, genre))
    # albums = get_albums(artist, album)
    albums = kodi.get_albums(artist=artist, album=album, genre=genre)

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
        speech("ik kan geen album "+album+" van "+artist+" vinden"+genretekst)
    elif rhasspy_confirm(confirmtext):
        speech(f"ik ga {str(len(albums))} afspelen {genretekst}")
        kodiplay_albums(albums)
    else:
        speech("okee dan niet")

def play_tracks_klassiek(artist="", composer="", matchtitle=""):
    log.debug("play_artist_album:(artist=%s, composer=%s, matchtitle==%s)"
              % (artist, composer, matchtitle))
    tracks = kodi.get_tracks_klassiek(artist, composer, matchtitle)
        
    if len(tracks) == 0:
        log.debug("play_tracks_klassiek:geen tracks gevonden")
        speech("ik kan geen treks "+matchtitle+" vinden")
    elif rhasspy_confirm(f"moet ik muziek {matchtitle} afspelen ?"):
        speech(f"ik ga de treks {matchtitle} afspelen")
        kodiplay_songs(tracks)
    else:
        speech("okee dan niet")

# def play_by_id(albumid):
    # albums = kodi.get_albuminfo(albumid)
    # if len(albums) == 0:
        # log.debug("kodiplay:geen album gevonden")
        # speech("ik kan geen album nummer "+str(albumid)+" vinden")
    # else:
        # kodiplay(albums)


# =============================================================================


def doConfirm():
    # Should not be called
    pass


def doDeny():
    speech("okee")


def doGetTime():
    now = datetime.datetime.now()
    speech("Het is nu  %s  uur en %d minuten " % (now.hour, now.minute))


def doTimer():
    minutes = get_slot_value("minutes")
    seconds = get_slot_value("seconds")
    command = PATH + 'timer.sh'
    seconds_to_sleep = minutes*60 + seconds
    log.debug("Call timer: [%s %d]" % (command, seconds_to_sleep))

    out = subprocess.Popen(['/bin/sh', command, str(seconds_to_sleep)],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    std_out, std_err = out.communicate()
    out = std_out.decode("utf-8")
    log.debug("doTimer:std_out=[%s]" % (str(out)))
    if (len(out) > 0):
        log.error(out)
        speech("Er is iets misgegaan met de timer. Ik ontving %s"
               % (out))
    else:
        log.debug("minutes:%d, seconds:%d" % (minutes,seconds))
        text_and = " en "
        if minutes == 0:
            text_minutes = ""
            text_and = ""
        else:
            if minutes == 1:
                text_minutes = " 1 minuut"
            else:
                text_minutes = str(minutes) + " minuten"

        if seconds == 0:
            text_seconds = ""
            text_and = ""
        else:
            text_seconds = str(seconds) + " seconden"

        log.debug("ik heb een taimer gezet op %s %s %s" % (text_minutes, text_and, text_seconds))
        speech("ik heb een taimer gezet op %s %s %s" % (text_minutes, text_and, text_seconds))


def doGetTemperature():
    res = get_domoticz("type=devices&rid="+temperatuur_idx)

    if res is not None:   # json result is Ok
        aantal_graden = str(res["Temp"])
        log.debug("Received: "+aantal_graden)
        speech("Het is buiten %s graden celsius"
               % (aantal_graden.replace(".", " komma ")))


def doGetWind():
    res = get_domoticz("type=devices&rid="+wind_idx)

    if res is not None:   # json result is Ok
        snelheidstr = res["Speed"]
        directionstr = res["DirectionStr"]
        log.debug("Received: "+snelheidstr+","+directionstr)
        speech("Het waait %s meter per seconde uit %selijke richting"
               % (snelheidstr.replace(".", " komma "), windnaam[directionstr]))
    else:
        speech("Geen antwoord van domoticz ontvangen")


def doGetElecticityUsage():
    res = get_domoticz("type=devices&rid="+electricity_idx)

    if res is not None:   # json result is Ok
        verbruikstr = res["Data"]
        log.debug("Received: "+verbruikstr)
        speech("Het elektriciteits verbruik is "+verbruikstr)
    else:
        speech("Geen antwoord van domoticz ontvangen")

def doDomo():
    name = get_slot_value("name")
    state = get_slot_value("state")
    idx = get_slot_value("idx")
    speech = get_slot_value("speech")


def doSceneAllesUit():
    domoScene("1")
    speech("welterusten")


def doSceneBezoek():
    domoScene("2")
    speech("hartelijk welkom bij Albert")


def doSceneTVKijken():
    domoScene("3")
    speech("veel plezier")


def doDimmer():
    idx = get_slot_value("idx", default=-1)
    state = get_slot_value("state",default="Off")
    level = get_slot_value("level", default=100)
    domoDimmer(idx, state, level)


def doSwitch():
    idx = get_slot_value("idx")
    state = get_slot_value("state")
    domoSwitch(idx, state)


def doMuziekKlassiek():
    '''
    [MuziekKlassiek]
    (speel:) (pianomuziek:piano|vioolmuziek:viool|cellomuziek:cello|pianoconcert|vioolconcert|celloconcert|nocturne|toccata|fuga|concert|suite){match} [van ($composers){composer}] [door ($artists){artist}]
    (speel:)  [(de:)|(het:)] (eerste:1|tweede:2|derde:no3|vierde:4|vijfde:5|zesde:6|zevende:7|achtste:8|negende:9){selectienum} (piano concert|viool concert|cello concert|brandenburger concert|symphonie){selectie} [van ($composers){composer}]
    Speel (symphonie [nummer:no.  (1..9) ] ){match}  [van ($composers){composer}]
    Speel [de|het] ($tracks){track}   [van ($composers){composer}]
    '''
    log.debug(f"doMuziekKlassiek")
    track = get_slot_value("track")
    log.debug(f"doMuziekKlassiek: track=>{track}<")
    selectie = get_slot_value("selectie")
    log.debug(f"doMuziekKlassiek: selectie=>{selectie}<")
    artist = get_slot_value("artist")
    composer = get_slot_value("composer")
    log.debug(f"play_tracks_klassiek(artist={artist}, composer={composer}, matchtitle={track}{selectie}")
    play_tracks_klassiek(artist=artist, composer=composer, matchtitle=track+selectie)

def doMuziekVanArtist():
    artist = get_slot_value("artist")
    play_artist_album(artist=artist)


def doMuziekVanAlbum():
    album = get_slot_value("album")
    play_artist_album(album=album)


def doMuziekVanAlbumArtist():
    artist = get_slot_value("artist")
    album = get_slot_value("album")
    play_artist_album(artist=artist, album=album)


def doMuziekVanGenre():
    genre = get_slot_value("genre")
    play_artist_album(genre=genre)


# def doMuziekAlbumid():
    # # speel album nummer  (0..500){albumid}
    # albumid = get_slot_value("albumid")
    # play_by_id(albumid)


def doMuziekAlbumlijstVanArtist():
    # welke albums (zijn er|hebben we) van ($artists){artist}
    speech("Ik kan nog geen lijst van albums geven")


def doMuziekPauseResume():
    kodi.pause_resume()


def doMuziekVolume():
    volume = get_slot_value("volume")
    kodi.volume(volume)


def doMuziekPrevious():
    kodi.previous_track()


def doMuziekNext():
    kodi.next_track()

def doMuziekWhatsPlaying():
    answer = kodi.get_whats_playing()
    log.debug(str(answer))
    if 'result' in answer and 'item' in answer['result']:
        item = answer['result']['item']
        album = item["album"]
        artist = item["artist"]
        title = item["title"]
        # genre = item["genre"]
        speech("Dit is het nummer, %s, van het album, %s, van, %s" 
               % (title, album, artist))
    else:
        speech("Ik weet het niet, sorry")


def doDuckDuckGo():
    artist = get_slot_value("artist")
    album = get_slot_value("album")
    genre = get_slot_value("genre")
    answer = get_duckduckgo(artist, album, genre)
    speech(answer)


# ============================================================================

if __name__ == '__main__':
    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s (%(lineno)d)'\
                 + '- %(message)s'
    logging.basicConfig(filename=PATH+'intenthandler.log',
                        level=logging.DEBUG,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')

    # get json from stdin and load into python dict
    log.debug("Intent received")
    jsonevent = json.loads(sys.stdin.read())
    log.debug("JSON:"+json.dumps(jsonevent))

    intent = jsonevent["intent"]["name"]
    log.info("Intent:"+intent)

    # kodi = Kodi(kodi_url, loglevel=-1, logfile="xxx.log")
    kodi = kodi.Kodi(kodi_url)

    # Call Intent handler do[Intent]():
    text_to_speak = get_slot_value("speech")
    speech(get_speech(text_to_speak))
    eval("do"+intent)()

    # convert dict to json and print to stdout
    returnJson = json.dumps(jsonevent)
    log.debug("JSON:"+returnJson)
    print(returnJson)
