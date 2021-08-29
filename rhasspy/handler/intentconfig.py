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

import os
import re
import logging
log = logging.getLogger(__name__)

from enum import Enum
Text = Enum('Text',
            'DecimalPoint AND MINUTE MINUTES SECONDS WEEKDAY MONTH' +
            ' ERROR Intent_Error DuckDuckGo_ERROR SENTENCES_ERROR' +
            ' Timer_Response Timer_ERROR GetTime_Response' +
            ' GetDate_Response GetAge_Response GetBirthDate_Response' +
            ' GetBirthDay_Single GetBirthDay_Multiple GetBirthDay_Month' +
            ' GetBirthDay_MonthList GetNoBirthDay')
DomoText = Enum('DomoText',
            'Error GetWind_Response GetWind_Direction')
KodiText = Enum('KodiText',
            'AskPlayConfirmation SayNoMusicFound SayPlayConfirmation' +
            ' SayNoPlayConfirmation WhatsPlaying_Response WhatsPlaying_Error')
# ------------------------------------------------------------
#     Configurable data
# ------------------------------------------------------------
 
config = {
    "urls" : 
        { "Rhasspy" : "http://localhost:12101"
        , "DuckDuckGo" : "https://api.duckduckgo.com"
        , "Domo" : "http://domopi:8080"
        , "Kodi" : "http://kodipi:8080"
        , "SmartCity" : "https://api.smartcitizen.me"
        }
    }

text = {
"en" : {
    Text.DecimalPoint: "point",
    Text.AND: "and",
    Text.MINUTE: "minute",
    Text.MINUTES: "minutes",
    Text.SECONDS: "seconds",
    Text.WEEKDAY: [ "monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday" ],
    Text.MONTH: [ "january", "febuary", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december" ],
    Text.ERROR: "something went wrong.  Please check the error in the logfile",
    Text.SENTENCES_ERROR: "something went wrong.  Please check the logfile for SENTENCES ERROR",
    Text.Intent_Error: "i cannot find intent {INTENT}",
    Text.DuckDuckGo_ERROR: "no information found for {SEARCH}",
    Text.Timer_Response: "i set a timer for {MINUTES} {AND} {SECONDS}",
    Text.Timer_ERROR: "i could not set a timer for less than 10 seconds",
    Text.GetTime_Response: "the time is  {HOURS} hours and {MINUTES} minutes",
    Text.GetDate_Response: "today is  {WEEKDAY} {MONTH} {DAY} {YEAR}",
    Text.GetAge_Response: ".birthday. is {YEARS} old",
    Text.GetBirthDate_Response: "{NAME} is born on {WEEKDAY} {MONTH} {DAY} {YEAR}",
    Text.GetBirthDay_Single: "Today is {NAME} s birthday",
    Text.GetBirthDay_Multiple: "Today is the birthay of: ",
    Text.GetBirthDay_Month: "birthdays are coming for: ",
    Text.GetBirthDay_MonthList : " {NAME} on {DATE} ",
    Text.GetNoBirthDay: "there are no birthdays in the coming month",
    DomoText.Error : "no answer received from domoticz",
    DomoText.GetWind_Response : \
        "the wind is blowing {SPEED} meter per second from the {DIRECTION}",
    DomoText.GetWind_Direction : {
            "N": "north",
            "NNE": "north north east",
            "NE": "north east",
            "ENE": "east north east",
            "E": "east",
            "ESE": "east south east",
            "SE": "south east",
            "SSE": "south south east",
            "S": "south",
            "SSW": "south south west",
            "SW": "south west",
            "WSW": "west south west",
            "W": "west",
            "WNW": "west north west",
            "NW": "north west",
            "NNW": "north north west"
        },
    KodiText.AskPlayConfirmation: "do you want me to play {TITLE} of {ARTIST} ?",
    KodiText.SayNoMusicFound: "i cannot find {ALBUM} of {ARTIST}",
    KodiText.SayPlayConfirmation: "i am going to play {TITLE} van {ARTIST}",
    KodiText.SayNoPlayConfirmation: "okay no music",
    KodiText.WhatsPlaying_Response : "this is track {TITLE}, of the album, {ALBUM}, of, {ARTIST}",
    KodiText.WhatsPlaying_Error: "i am sorry, but i do not know"
    },
"nl" : {
    Text.DecimalPoint: "komma",
    Text.AND: "en",
    Text.MINUTE: "minuut",
    Text.MINUTES: "minuten",
    Text.SECONDS: "seconden",
    Text.WEEKDAY: [ "maandag", "dinsdag", "woensdag",
        "donderdag", "vrijdag", "zaterdag", "zondag" ],
    Text.MONTH: [ "januari", "febuari", "maart", "april", "mei", "juni",
        "juli", "augustus", "september", "october", "november", "december" ],
    Text.ERROR: "Er is iets fout gegaan. zoek in het log bestand naar error",
    Text.SENTENCES_ERROR: "Er is iets fout gegaan. zoek in het log bestand naar SENTENCES ERROR",
    Text.DuckDuckGo_ERROR: "Geen informatie gevonden voor {SEARCH}",
    Text.Timer_Response: "ik heb een taimer gezet op {MINUTES} {AND} {SECONDS}",
    Text.Timer_ERROR: "ik kan geen taimer zetten voor minder dan 10 seconden",
    Text.GetTime_Response: "Het is nu  {HOURS}  uur en {MINUTES} minuten",
    Text.GetDate_Response: "het is vandaag {WEEKDAY} {DAY} {MONTH} {YEAR}",
    Text.GetAge_Response: ".birthday. is {YEARS}",
    Text.GetBirthDate_Response: "{NAME} is geboren op {WEEKDAY} {DAY} {MONTH} {YEAR}",
    Text.GetBirthDay_Single: "Vandaag is de verjaardag van: {NAME}",
    Text.GetBirthDay_Multiple: "Vandaag is de verjaardag van: ",
    Text.GetBirthDay_Month: "komende verjaardagen zijn:  ",
    Text.GetBirthDay_MonthList : " {NAME} op {DATE} ",
    Text.GetNoBirthDay: "de rest van de maand en de volgende maand zijn er geen verjaardagen",

    DomoText.Error : "Geen of fout antwoord van domoticz ontvangen",
    DomoText.GetWind_Response : "Het waait {SPEED} meter per seconde uit {DIRECTION}elijke richting",
    DomoText.GetWind_Direction : {
            "N": "noord",
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
            "NNW": "noord noord west"
        },
    KodiText.AskPlayConfirmation: "wil je dat ik {TITLE} van {ARTIST} ga afspelen ?",
    KodiText.SayNoMusicFound: "ik kan geen album {ALBUM} van {ARTIST} vinden",
    KodiText.SayPlayConfirmation: "ik ga {TITLE} van {ARTIST} afspelen",
    KodiText.SayNoPlayConfirmation: "okee, dan niet",
    KodiText.WhatsPlaying_Response : "Dit is het nummer, {TITLE},van het album, {ALBUM}, van, {ARTIST}",
    KodiText.WhatsPlaying_Error: "Ik weet het niet, sorry"
    }
}

# ------------------------------------------------------------
#     End of Configurable data
#     Do not change below this line 
#     Unless you know what your doing
# ------------------------------------------------------------
 

def get_language():
    PROFILEDIR = os.getenv("RHASSPY_PROFILE_DIR",default="nl")
    return re.sub(".*/(..)$","\\1",PROFILEDIR)

def get_text(textid=Text.ERROR,textsubid=None):
    lang = get_language()
    default_lang = "nl"
    if not lang in text:
        lang = default_lang

    if textid in text[lang]:
        if textsubid is None:
            return text[lang][textid]
        elif textsubid in text[lang][textid]:
            return text[lang][textid][textsubid]

    return text[lang][Text.ERROR]

def get_url(key):
    return config["urls"][key]

def replace_decimal_point(str_in):
    decimal_point = get_text(Text.DecimalPoint)
    return str_in.replace(".", f" {decimal_point} ")
    
def get_instances(json):
    instances = {}
    if "Domo" in config["urls"]:
        from intentdomo import IntentDomo
        instances["Domo"] = IntentDomo(json)
    if "Kodi" in config["urls"]:
        from intentkodi import IntentKodi
        instances["Kodi"] = IntentKodi(json)
    if "SmartCity" in config["urls"]:
        from intentsmartcity import IntentSmartCity
        instances["SmartCity"] = IntentSmartCity(json)
    return instances

def get_slots(filename):
    fslots = open(filename, "r")
    lines = fslots.read().splitlines()
    fslots.close()
    slots = {}
    for l in lines:
        line = l.split(':')
        if len(line) == 2:
            name = re.sub('[)(]', '', line[0])
            date = line[1]
            slots[name] = date
    return slots
