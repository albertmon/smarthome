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
from intentjson import IntentJSON
import intentconfig
import traceback
from intentexcept import error_missing_parameter
from intentexcept import SentencesError

log = logging.getLogger(__name__)

PROFILEDIR = os.getenv("RHASSPY_PROFILE_DIR", default=".")
HANDLERDIR = f"{PROFILEDIR}/handler/"
LOGPATH = HANDLERDIR


def get_duckduckgo(search):
    if "DuckDuckGo" in intentconfig.config["urls"]:
        duckduckgo_url = intentconfig.config["urls"]["DuckDuckGo"]
    else:
        return("Configuratie fout: Geen url voor duckduckgo gevonden")

    language = intentconfig.get_language()
    language_code = language + "-" + language
    params = {'q': search, 'kl': language_code, 'format': 'json'}

    log.debug(f"duckduckgo({search})")
    try:
        res = requests.get(duckduckgo_url, params=params)
        if res.status_code != 200:
            log.info(f"Url:[{duckduckgo_url}]")
            log.info("Result:{res.status_code}, text:{res.text}")
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
# All intent handlers start with do followed by the intent name (Case Sensitive!)



def doDummy():
    pass


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

def getDateStrings(date_time):
    weekdays = intentconfig.get_text(intentconfig.Text.WEEKDAY)
    months = intentconfig.get_text(intentconfig.Text.MONTH)
    weekday = weekdays[date_time.weekday()]  # monday = 0
    day = date_time.day
    month = months[date_time.month-1]  # index starts at 0
    year = date_time.year
    return (weekday, day, month, year)

def doGetDate():
    now = datetime.datetime.now()
    (weekday, day, month, year) = getDateStrings(now)
    speech = intentconfig.get_text(intentconfig.Text.GetDate_Response).\
        format(WEEKDAY=weekday, DAY=day, MONTH=month, YEAR=year)

    intentjson.set_speech(speech)

def doTimer():
    minutes = int(intentjson.get_slot_value("minutes","0"))
    seconds = int(intentjson.get_slot_value("seconds","0"))
    PATH = os.getenv("RHASSPY_PROFILE_DIR") + "/handler/"
    command = PATH + 'timer.sh'
    seconds_to_sleep = minutes*60 + seconds
    log.debug(f"Call timer: [{command}, {seconds_to_sleep}]")

    if seconds_to_sleep < 10:
        speech = intentconfig.get_text(intentconfig.Text.Timer_ERROR)
        intentjson.set_speech(speech)
        return

    out = subprocess.Popen(['/bin/sh', command, str(seconds_to_sleep)],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    std_out, std_err = out.communicate()
    result = std_out.decode("utf-8")
    log.debug(f"doTimer:std_out=[{result}]")
    if (len(result) > 0):
        log.error(f"== ERROR =v= ERROR ==\n{result}\n== ERROR =^= ERROR ==")
        speech = intentconfig.get_text(intentconfig.Text.Timer_ERROR)
        intentjson.set_speech(speech)
    else:
        log.debug(f"minutes:{minutes}, seconds:{seconds}")
        text_and = intentconfig.get_text(intentconfig.Text.AND)
        if minutes == 0:
            text_minutes = ""
            text_and = ""
        elif minutes == 1:
            text_minutes = f"1 {intentconfig.get_text(intentconfig.Text.MINUTE)}"
        else:
            text_minutes = f"{minutes} {intentconfig.get_text(intentconfig.Text.MINUTES)}"

        if seconds == 0:
            text_seconds = ""
            text_and = ""
        else:
            text_seconds = f"{seconds} {intentconfig.get_text(intentconfig.Text.SECONDS)}"

        log.debug(f"Timer set. Text:{text_minutes} {text_and} {text_seconds}")
        speech = intentconfig.get_text(intentconfig.Text.Timer_Response).\
            format(MINUTES=text_minutes, AND=text_and, SECONDS=text_seconds)
        intentjson.set_speech(speech)

def getStringAsDate(s):
    log.debug(f"getStringAsDate:s=[{s}]")
    if re.match(r"\d{4}-\d{1,2}-\d{1,2}", s) :
        date = datetime.datetime.strptime(s,"%Y-%m-%d")
    elif re.match(r"\d{1,2}-\d{1,2}-\d{4}", s) :
        date = datetime.datetime.strptime(s,"%d-%m-%Y")
    else:
        date = None
    return date

def getNameAndBirthdate():
    name = intentjson.get_raw_value("birthday")
    if not name:
        error_missing_parameter("birthday","GetAge")
    birthday = intentjson.get_slot_value("birthday")
    if not name:
        error_missing_parameter("birthday","GetAge")
    log.debug(f"doGetAge, name=<{name}>, birthday=[{birthday}]")
    birthdate = getStringAsDate(birthday)
    if not birthdate:
        error_missing_parameter("birthday","GetAge")
    return (name, birthdate)

def doBirthDay():
    (name, birthdate) = getNameAndBirthdate()
    (weekday, day, month, year) = getDateStrings(birthdate)
    speech = intentconfig.get_text(intentconfig.Text.GetBirthDate_Response).\
        format(WEEKDAY=weekday, DAY=day, MONTH=month, YEAR=year, NAME=name)

    intentjson.set_speech(speech)

def doGetAge():
    (name, birthdate) = getNameAndBirthdate()
    today = datetime.date.today()
    age = today.year - birthdate.year
    if ((today.month, today.day) < (birthdate.month, birthdate.day)):
        age = age - 1  # birthday not yet passed
    speech = intentconfig.get_text(intentconfig.Text.GetAge_Response)
    speech = intentjson.get_speech(speech)
    log.debug(f"age={age}, speech=[{speech}]")
    speech = speech.replace('YEARS',str(age))
    intentjson.set_speech(speech)

def doBirthDays():
    today = datetime.date.today()
    slotsfile = os.getenv("RHASSPY_PROFILE_DIR") + "/slots/birthdays"
    slots = intentconfig.get_slots(slotsfile)

    birthday_persons = ""
    born_this_month = {}
    for name, birthday in slots.items():
        birthdate = getStringAsDate(birthday)
        if birthdate.month == today.month:
            if birthdate.day == today.day:
                if len(birthday_persons) > 0:
                    and_string = intentconfig.get_text(intentconfig.Text.AND)
                    birthday_persons = f"{birthday_persons} {and_string} "
                birthday_persons = birthday_persons + name
            elif birthdate.day > today.day:
                born_this_month[name] = birthdate
        elif birthdate.month == (today.month+1)%12 \
            and birthdate.day <= today.day:  # birthday next month?:
            born_this_month[name] = birthdate
 
    log.debug(f"birthday_persons:[{birthday_persons}]\n"\
        + f"   born_this_month:[{str(born_this_month)}]")

    if len(birthday_persons) == 1 :
        speech = intentconfig.get_text(intentconfig.Text.GetBirthDay_Single)
        speech = speech.format(NAME=birthday_persons[0])
    elif len(birthday_persons) > 1 :
        speech = intentconfig.get_text(intentconfig.Text.GetBirthDay_Multiple)
        speech = speech + birthday_persons
    else:
        speech = ""

    if len(born_this_month) > 0 :
        text = intentconfig.get_text(intentconfig.Text.GetBirthDay_Month)
        months = intentconfig.get_text(intentconfig.Text.MONTH)
        list_string = intentconfig.get_text(intentconfig.Text.GetBirthDay_MonthList)
        log.debug(f"list_string=[{list_string}]")
        names = ""
        and_string = ": " + intentconfig.get_text(intentconfig.Text.AND) + " "
        for name, birthdate in born_this_month.items():
            datestr = f" {birthdate.day} {months[birthdate.month-1]} "
            if names:
                names = names + and_string
            names = names + list_string.format(NAME=name,DATE=datestr)
            log.debug(f"names={names}, name={name}, DATE={datestr}")
        speech = speech + ": " + text + " " + names

    if not speech:
        speech = intentconfig.get_text(intentconfig.Text.GetNoBirthDay)

    intentjson.set_speech(speech)

def doDuckDuckGo():
    slots = intentjson.get_slot_value("slots")
    searchstring = ""
    for slot in re.sub("[^A-Za-z0-9]", " ",  slots).split():
        value = intentjson.get_slot_value(slot)
        log.debug(f"slot={slot}, value={value}.")
        searchstring = searchstring + value + " "
    text = get_duckduckgo(searchstring.strip())
    intentjson.set_speech(text)


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

    try:
        intentcalled = False
        for (key, intentinstance) in\
                intentconfig.get_instances(intentjson).items():
            log.debug(f"Trying intent{key}.do{intent}")
            if intent.startswith(key):
                try:
                    log.debug(f"Calling intent{key}.do{intent}")
                    eval(f"intentinstance.do"+intent)()
                    intentcalled = True
                    break  # Dirty programming!
                except AttributeError:
                    log.debug(f"{traceback.format_exc()}")
                    continue  # Dirty programming!

        if not intentcalled:
            try:
                log.debug(f"Calling default intent do{intent}")
                eval("do"+intent)()
            except NameError:
                log.debug(f"{traceback.format_exc()}")
                speech = intentconfig.get_text(intentconfig.Text.Intent_Error)
                intentjson.set_speech(speech.format(INTENT=intent))
    except SentencesError as se:
        speech = se.handle()
        intentjson.set_speech(speech)

    # convert dict to json and print to stdout
    returnJson = intentjson.get_json_as_string()
    log.debug(f"JSON:{returnJson}")
    print(returnJson)
