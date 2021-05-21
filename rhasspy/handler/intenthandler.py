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
import logging
import re
log = logging.getLogger(__name__)

from intentjson import IntentJSON
import intentconfig
import traceback


PROFILEDIR = os.getenv("RHASSPY_PROFILE_DIR",default=".")
HANDLERDIR = f"{PROFILEDIR}/handler/"
LOGPATH = HANDLERDIR


def get_duckduckgo(search):
    if "DuckDuckGo" in intentconfig.config["urls"]:
        duckduckgo_url = intentconfig.config["urls"]["DuckDuckGo"]
    else:
        return("Configuratie fout: Geen url voor duckduckgo gevonden")

    language = intentconfig.get_language()
    language_code = language + "-" + language
    params = { 'q': search, 'kl': language_code, 'format': 'json' }

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
        result = intentconfig.get_text(intentconfig.Text.DuckDuckGo_ERROR)
        return(result.format(SEARCH=search))
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
    hour = now.hour
    minutes = now.minute
    speech = intentconfig.get_text(intentconfig.Text.GetTime_Response)
    intentjson.set_speech(speech.format(HOURS=hour, MINUTES=minutes))


def doTimer():
    minutes = intentjson.get_slot_value("minutes")
    seconds = intentjson.get_slot_value("seconds")
    PATH = os.getenv("RHASSPY_PROFILE_DIR") + "/handler/"
    command = PATH + 'timer.sh'
    seconds_to_sleep = minutes*60 + seconds
    log.debug(f"Call timer: [{command}, {seconds_to_sleep}]")

    out = subprocess.Popen(['/bin/sh', command, str(seconds_to_sleep)],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    std_out, std_err = out.communicate()
    result = std_out.decode("utf-8")
    log.debug(f"doTimer:std_out=[{result}]")
    if (len(result) > 0):
        log.error(result)
        speech = intentconfig.get_text(intentconfig.Text.GetTime_ERROR)
        intentjson.set_speech(speech.format(MESSAGE=result))
    else:
        log.debug(f"minutes:{minutes}, seconds:{seconds}")
        text_and = intentconfig.get_text(intentconfig.Text.AND)
        if minutes == 0:
            text_minutes = ""
            text_and = ""
        elif minutes == 1:
            text_minutes = "1 "+intentconfig.get_text(intentconfig.Text.MINUTE)
        else:
            text_minutes = str(minutes)+ " " + intentconfig.get_text(intentconfig.Text.MINUTES)

        if seconds == 0:
            text_seconds = ""
            text_and = ""
        else:
            text_seconds = str(seconds) + " " + intentconfig.get_text(intentconfig.Text.SECONDS)

        log.debug(f"ik heb een taimer gezet op {text_minutes} {text_and} {text_seconds}")
        speech = intentconfig.get_text(intentconfig.Text.Timer_Response)
        intentjson.set_speech(speech.format(MINUTES=text_minutes, AND=text_and, SECONDS=text_seconds))

def doDuckDuckGo():
    slots = intentjson.get_slot_value("slots")
    searchstring = ""
    for slot in re.sub("[^\w]", " ",  slots).split():
        value = intentjson.get_slot_value(slot);
        log.debug(f"slot={slot}, value={value}.")
        searchstring = searchstring + value
    text = get_duckduckgo(searchstring)
    intentjson.set_speech(text)

def doDummy():
    pass

# ============================================================================

if __name__ == '__main__':
    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s (%(lineno)d)'\
                 + '- %(message)s'
    logging.basicConfig(filename=LOGPATH+'intenthandler.log',
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
            log.debug(f"{traceback.format_exc()}")
            speech = intentconfig.get_text(intentconfig.Text.Intent_Error)
            intentjson.set_speech(speech.format(INTENT=intent))

    # convert dict to json and print to stdout
    returnJson = intentjson.get_json_as_string()
    log.debug(f"JSON:{returnJson}")
    print(returnJson)
