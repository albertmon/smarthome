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
import datetime
import requests
import subprocess

from intentjson import IntentJSON
from intentkodi import IntentKodi
from rhasspy import Rhasspy
from kodi import Kodi


import logging
log = logging.getLogger(__name__)

PATH = "/profiles/nl/handler/"

duckduckgo_url = 'https://api.duckduckgo.com/?'
domoticz_url = "http://192.168.0.3:8080/json.htm?"
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

def get_domoticz(command):
    url = domoticz_url+command
    log.debug("Url:"+url)
    try:
        res = requests.get(url)
        if res.status_code != 200:
            log.info(f"Url:[{url}\nResult:{res.status_code}, text:{res.text}")
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
            search = f"album {album} {artist}"
        else:
            search = artist

    params = { 'q': search, 'kad': 'nl_NL', 'kl': 'nl-nl', 'format': 'json' }

    log.debug(f"duckduckgo({search})")
    try:
        res = requests.get(duckduckgo_url, params=params)
        if res.status_code != 200:
            log.info(f"Url:[{duckduckgo_url}]\nResult:{res.status_code}, text:{res.text}")
    except ConnectionError:
        log.error(f"ConnectionError for url {duckduckgo_url}")

    log.debug(str(res.text))
    res_json = json.loads(res.text)

    if res_json["AbstractText"] is None or res_json["AbstractText"] == "":
        return(f"Geen informatie over {search} gevonden")
    else:
        return(res_json["AbstractText"])


# ================  Intent handlers =================================

def domoInfo(idx, field_name, defaultValue=""):
      # "Level": 80,
      # "LevelInt": 12,
      # "MaxDimLevel": 15,
      # "Name": "Tafellicht",

    res_json = get_domoticz(f"type=devices&rid={idx}")
    log.debug("Domotcz result: "+str(res_json))
    if field_name in res_json:
        value = res_json[field_name]
    else:
        value = defaultValue
    if "Name" in res_json:
        domo_name = res_json["Name"]
    else:
        domo_name = ""
    return (value, domo_name)

def domoDimmer(idx, state, level=-1):
    log.debug(f"domoDimmer({idx}, {state}, {level})")
    if level >= 0:
        (maxDimLevel,name) = domoInfo(idx,"MaxDimLevel","100")
        log.debug(f"(maxDimLevel={maxDimLevel},name={name})")
        level = int((level * int(maxDimLevel))/100 + 0.5)
        switchcmd = "Set Level&level=%d" % (level)
    else:
        switchcmd = state
    command = f"type=command&param=switchlight&idx={idx}&switchcmd={switchcmd}"
    get_domoticz(command)


def domoSwitch(idx, state):
    command = f"type=command&param=switchlight&idx={idx}&switchcmd={state}"
    log.debug(f"domoSwitch:command={command}")
    get_domoticz(command)


def domoScene(idx):
    command = f"type=command&param=switchscene&idx={idx}&switchcmd=On"
    get_domoticz(command)


# =============================================================================

def doConfirm():
    # Should not be called
    # Used by Rhasspy conversation
    pass


def doDeny():
    intentjson.set_speech("okee")


def doGetTime():
    now = datetime.datetime.now()
    intentjson.set_speech("Het is nu  %s  uur en %d minuten " % (now.hour, now.minute))


def doTimer():
    minutes = intentjson.get_slot_value("minutes")
    seconds = intentjson.get_slot_value("seconds")
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
        intentjson.set_speech("Er is iets misgegaan met de timer. Ik ontving %s"
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
        intentjson.set_speech("ik heb een taimer gezet op %s %s %s" % (text_minutes, text_and, text_seconds))

def doGetWind():
    res = get_domoticz("type=devices&rid="+wind_idx)

    if res is not None:   # json result is Ok
        snelheidstr = res["Speed"]
        directionstr = res["DirectionStr"]
        log.debug("Received: "+snelheidstr+","+directionstr)
        intentjson.set_speech("Het waait %s meter per seconde uit %selijke richting"
               % (snelheidstr.replace(".", " komma "), windnaam[directionstr]))
    else:
        intentjson.set_speech("Geen antwoord van domoticz ontvangen")


def doDomoInfo():
    field_name = intentjson.get_slot_value("name")
    idx = intentjson.get_slot_value("idx")
    resultString = intentjson.get_slot_value("speech")
    resultMatch = intentjson.get_slot_value("result","RESULT")
    
    (value, domo_name) = domoInfo(idx, field_name)
    returnValue = str(value).replace("."," komma ")
    intentjson.set_speech(resultString.replace(resultMatch,returnValue))

def doDomoScene():
    name = intentjson.get_slot_value("name")
    state = intentjson.get_slot_value("state")
    idx = intentjson.get_slot_value("idx")
    intentjson.set_speech(intentjson.get_slot_value("speech"))
    command = f"type=command&param=switchscene&idx={idx}&switchcmd=On"
    get_domoticz(command)


def doDomoDimmer():
    idx = intentjson.get_slot_value("idx", default=-1)
    state = intentjson.get_slot_value("state",default="Off")
    level = intentjson.get_slot_value("level", default=100)
    domoDimmer(idx, state, level)


def doDomoSwitch():
    idx = intentjson.get_slot_value("idx")
    state = intentjson.get_slot_value("state")
    log.debug(f"doSwitch:idx={idx},state={state}")
    domoSwitch(idx, state)


def doDuckDuckGo():
    artist = intentjson.get_slot_value("artist")
    album = intentjson.get_slot_value("album")
    genre = intentjson.get_slot_value("genre")
    answer = intentjson.get_duckduckgo(artist, album, genre)
    intentjson.set_speech(answer)


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
    inputjson = json.loads(sys.stdin.read())
    log.debug("JSON:"+json.dumps(inputjson))
    intentjson = IntentJSON(inputjson)
    intent = intentjson.get_intent()
    log.info("Intent:"+intent)


    # Call Intent handler do[Intent]():
    text_to_speak = intentjson.get_slot_value("speech")
    intentjson.set_speech(intentjson.get_speech(text_to_speak))
    try:
        eval("do"+intent)()
    except NameError:
        try:
            # kodi = Kodi(kodi_url, loglevel=-1, logfile="xxx.log")
            kodi = Kodi(kodi_url)
            rhasspy = Rhasspy(rhasspy_url)
            log.debug(f"Calling IntentKodi")
            intentkodi = IntentKodi(intentjson, kodi, rhasspy)
            log.debug(f"Calling intentkodi.do{intent}")
            eval("intentkodi.do"+intent)()
        except NameError:
            intentjson.set_speech(f"ik kan geen intent {intent} vinden")

    # convert dict to json and print to stdout
    returnJson = intentjson.get_json_as_string()
    log.debug("JSON:"+returnJson)
    print(returnJson)
