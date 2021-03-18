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
from kodimusic import Music

import logging
log = logging.getLogger(__name__)

PATH = "/profiles/nl/handler/"
musicfile = PATH + "music"

duckduckgo_url = 'https://api.duckduckgo.com/?'
domticz_url = "http://192.168.0.3:8080/json.htm?"
kodi_url = "http://192.168.0.5:8080/jsonrpc"

# map names to domoticz idx
lampen = {"boekenkastlamp": "1",
          "tvlamp": "3",
          "oranje lamp": "2",
          "lamp bij zijraam": "4",
          "leeslamp": "4",
          "bureaulamp": "11",
          "tafellicht": "5"}
temperatuur_idx = "19"
wind_idx = "20"
electricity_idx = "6"

states = {"aan": "On", "uit": "Off"}
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


def domoDimmer(name, state):
    log.debug("domoDimmer("+name+","+state+")")
    command = "type=command&param=switchlight&idx=%s&switchcmd=%s"\
        % (lampen[name], states[state])
    get_domoticz(command)
    # to set level : &switchcmd=Set%20Level&level=6


def domoSwitch(name, state):
    command = "type=command&param=switchlight&idx=%s&switchcmd=%s"\
        % (lampen[name], states[state])
    get_domoticz(command)


def domoScene(idx):
    command = "type=command&param=switchscene&idx=%s&switchcmd=On" % (idx)
    get_domoticz(command)


def kodiplay(albums):
    log.debug("kodiplay:gotAlbums:%s" % (str(albums)))
    kodi.clear_playlist()
    log.debug("albums[0]=%s" % (str(albums[0])))
    for album in albums:
        log.debug("album=%s" % (str(album)))

        if len(albums) == 1:
            speech("Ik ga het album %s van %s afspelen"
                   % (album["album"], album["artistsearch"]))

        log.debug("Ik ga het album %s (%s) van %s op playlist zetten" %
                  (album["id"], album["album"], album["artistsearch"]))
        kodi.add_album_to_playlist(album["id"])
    kodi.restart_play()


def play_artist_album(artist="", album="", genre=""):
    log.debug("play_artist_album:(artist=%s, album=%s, genre=%s)"
              % (artist, album, genre))
    # albums = get_albums(artist, album)
    music = Music(kodi, musicfile)
    albums = music.search_albuminfo(artist=artist, album=album, genre=genre)
    if genre is not None:
        genretekst = " in het genre " + genre
    else:
        genretekst = ""
    if len(albums) == 0:
        log.debug("kodiplay:geen album gevonden")
        if artist == "":
            artist = "een wilekeurige artiest"
        speech("ik kan geen album "+album+" van "+artist+" vinden"+genretekst)
    else:
        speech("ik ga alle albums van %s afspelen%s" % (artist, genretekst))
        kodiplay(albums)


def play_by_id(albumid):
    music = Music(kodi, musicfile)
    albums = music.get_albuminfo(albumid)
    if len(albums) == 0:
        log.debug("kodiplay:geen album gevonden")
        speech("ik kan geen album nummer "+str(albumid)+" vinden")
    else:
        kodiplay(albums)


# =============================================================================


def doDummy():
    speech("okee")


def doGetTime():
    now = datetime.datetime.now()
    speech("Het is nu  %s  uur en %d minuten " % (now.hour, now.minute))


def doTimer():
    minutes = jsonevent["slots"]["minutes"]
    seconds = jsonevent["slots"]["seconds"]
    command = PATH + 'timer.sh'
    secondsToSleep = int(minutes)*60 + int(seconds)
    log.debug("Call timer: [%s %d]" % (command, secondsToSleep))

    out = subprocess.Popen(['/bin/sh', command, str(secondsToSleep)],
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
        speech("ik heb een taimer gezet op %d seconden " % (secondsToSleep))


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


def doSceneAllesUit():
    domoScene("1")
    speech("welterusten")


def doSceneBezoek():
    domoScene("2")
    speech("hartelijk welkom bij Albert")


def doSceneTVKijken():
    domoScene("3")
    speech("veel plezier")


def doTafellichtAanUit():
    name = "tafellicht"    # jsonevent["slots"]["name"]
    state = jsonevent["slots"]["state"]
    domoDimmer(name, state)
    speech("Ik heb de %s %s gedaan" % (name, state))


def doChangeLightState():
    name = jsonevent["slots"]["name"]
    state = jsonevent["slots"]["state"]
    domoSwitch(name, state)
    speech("Ik heb de %s %s gedaan" % (name, state))

def doMuziekVanArtist():
    artist = jsonevent["slots"]["artist"]
    play_artist_album(artist=artist)


def doMuziekVanAlbum():
    album = jsonevent["slots"]["album"]
    play_artist_album(album=album)


def doMuziekVanAlbumArtist():
    artist = jsonevent["slots"]["artist"]
    album = jsonevent["slots"]["album"]
    play_artist_album(artist=artist, album=album)


def doMuziekVanGenre():
    genre = jsonevent["slots"]["genre"]
    play_artist_album(genre=genre)


def doMuziekAlbumid():
    # speel album nummer  (0..500){albumid}
    albumid = jsonevent["slots"]["albumid"]
    play_by_id(albumid)


def doMuziekAlbumlijstVanArtist():
    # welke albums (zijn er|hebben we) van ($artists){artist}
    speech("Ik kan nog geen lijst van albums geven")


def doMuziekPauseResume():
    kodi.pause_resume()


def doMuziekVolume():
    volume = jsonevent["slots"]["volume"]
    kodi.volume(volume)


def doMuziekPrevious():
    kodi.previous_track()


def doMuziekNext():
    kodi.next_track()

def doMuziekWhatsPlaying():
    answer = kodi.get_whats_playing()
    log.debug(str(answer))
    if answer['result'] is not None and answer['result']['item'] is not None:
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
    if "artist" in jsonevent["slots"]:
        artist = jsonevent["slots"]["artist"]
    else:
        artist = ""

    if "album" in jsonevent["slots"]:
        album = jsonevent["slots"]["album"]
    else:
        album = ""
    if "genre" in jsonevent["slots"]:
        genre = jsonevent["slots"]["genre"]
    else:
        genre = ""
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
    eval("do"+intent)()

    # convert dict to json and print to stdout
    returnJson = json.dumps(jsonevent)
    log.debug("JSON:"+returnJson)
    print(returnJson)
