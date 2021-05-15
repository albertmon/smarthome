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
import os
import time
import json
import datetime
import requests
import subprocess

from intentjson import IntentJSON


import logging
log = logging.getLogger(__name__)

LOGPATH = "/profiles/nl/handler/"
SHPATH = "/profiles/nl/handler/"
domoticz_url = "http://192.168.0.3:8080/json.htm?"
kodi_url = "http://192.168.0.5:8080/jsonrpc"
rhasspy_url = "http://192.168.0.3:12101/api/"

duckduckgo_url = 'https://api.duckduckgo.com/?'

wind_idx = "20"

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
    seconds_to_sleep = minutes*60 + seconds
    audiodevice = profilejson["sounds"]["aplay"]["device"]
    soundfile = intentjson.get_slot_value("soundfile","handler/alarm_clock_1.wav")
    if os.fork() == 0:
        time.sleep(seconds_to_sleep)
        out = subprocess.run(['aplay', '-D', audiodevice, PROFILEDIR+soundfile])
        if out is None or out.returncode != 0:
            sys.exit(1)
        sys.exit(0)
    else:
        if minutes == 0:
            text_minutes = ""
        else:
            if minutes == 1:
                text_minutes = " 1 minuut"
            else:
                text_minutes = str(minutes) + " minuten"

        if seconds == 0:
            text_seconds = ""
        else:
            text_seconds = str(seconds) + " seconden"

        if seconds == 0 or minutes == 0:
            text_and = "en "
        else:
            text_and = ""
        text = "ik heb een taimer gezet op {text_minutes} {text_and}{text_seconds}"
        log.debug(text)
        intentjson.set_speech(text)

# ============================================================================

if __name__ == '__main__':
    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s (%(lineno)d)'\
                 + '- %(message)s'
    logging.basicConfig(filename=LOGPATH+'intenthandler.log',
                        level=logging.DEBUG,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')

    # get profile json from file
    PROFILEDIR=os.getenv("RHASSPY_PROFILE_DIR")
    if PROFILEDIR != "":
        PROFILEDIR = PROFILEDIR + "/"
    profile = open(PROFILEDIR+'profile.json', 'r')
    profilejson = json.loads(profile.read())

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
    
    import intentconfig
    intentcalled = False
    for (key,intentinstance) in intentconfig.get_instances(intentjson).items():
        log.debug(f"Trying intent{key}.do{intent}")
        if intent.startswith(key):
            try:
                log.debug(f"Calling intent{key}.do{intent}, type={type(intentinstance)}")
                eval(f"intentinstance.do"+intent)()
                intentcalled = True
                break # Dirty programming!
            except AttributeError:
                log.debug(f"{traceback.format_exc()}")
                continue # Dirty programming!

    if intentcalled == False:
        try:
            log.debug(f"Calling default intent do{intent}")
            eval("do"+intent)()
        except NameError:
            intentjson.set_speech(f"ik kan geen intent {intent} vinden")

    # convert dict to json and print to stdout
    returnJson = intentjson.get_json_as_string()
    log.debug("JSON:"+returnJson)
    print(returnJson)
