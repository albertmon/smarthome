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


def do_get(url):
    log.debug("do_get Url:"+url)
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
    json_result = json.loads(res.text)
    log.debug(str(json_result))
    if "result" in json_result:
        return(json_result["result"][0])

    return(None)

# ================  Intent handlers =================================


def domoDimmer(name, state):
    log.debug("domoDimmer("+name+","+state+")")
    command = "type=command&param=switchlight&idx=%s&switchcmd=%s"\
        % (lampen[name], states[state])
    do_get(domticz_url + command)
    # to set level : &switchcmd=Set%20Level&level=6


def domoSwitch(name, state):
    command = "type=command&param=switchlight&idx=%s&switchcmd=%s"\
        % (lampen[name], states[state])
    do_get(domticz_url + command)


def domoScene(idx):
    command = "type=command&param=switchscene&idx=%s&switchcmd=On" % (idx)
    do_get(domticz_url + command)


def play(artist, album):
    log.debug("play:(artist=%s, album=%s)" % (artist, album))
    # albums = get_albums(artist, album)
    music = Music(kodi, musicfile)
    albums = music.search_albuminfo(artist, album)
    log.debug("play:gotAlbums:%s" % (str(albums)))
    if len(albums) == 0:
        log.debug("play:geen album gevonden")
        if artist == "":
            artist = "een wilekeurige artiest"
        if album == "":
            album = "een willekeurig album"
        speech("ik kan geen album "+album+" van "+artist+" vinden")
    else:
        kodi.clear_playlist()
        speech("ik ga alle albums van %s afspelen" % (artist))
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
    res = do_get(domticz_url + "type=devices&rid="+temperatuur_idx)

    if res is not None:   # json result is Ok
        aantal_graden = str(res["Temp"])
        log.debug("Received: "+aantal_graden)
        speech("Het is buiten %s graden celsius"
               % (aantal_graden.replace(".", " komma ")))


def doGetWind():
    res = do_get(domticz_url + "type=devices&rid="+wind_idx)

    if res is not None:   # json result is Ok
        snelheidstr = res["Speed"]
        directionstr = res["DirectionStr"]
        log.debug("Received: "+snelheidstr+","+directionstr)
        speech("Het waait %s meter per seconde uit %selijke richting"
               % (snelheidstr.replace(".", " komma "), windnaam[directionstr]))
    else:
        speech("Geen antwoord van domoticz ontvangen")


def doGetElecticityUsage():
    res = do_get(domticz_url + "type=devices&rid="+electricity_idx)

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
    album = ""
    play(artist, album)


def doMuziekVanAlbum():
    artist = ""
    album = jsonevent["slots"]["album"]
    play(artist, album)


def doMuziekVanAlbumArtist():
    artist = jsonevent["slots"]["artist"]
    album = jsonevent["slots"]["album"]
    play(artist, album)


def doMuziekPauseResume():
    kodi.pause_resume()


def doMuziekVolume():
    volume = jsonevent["slots"]["volume"]
    kodi.volume(volume)


def doMuziekPrevious():
    kodi.previous_track()


def doMuziekNext():
    kodi.next_track()


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
