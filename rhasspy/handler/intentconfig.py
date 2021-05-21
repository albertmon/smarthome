#!/usr/bin/env python
import os
import re
import logging
log = logging.getLogger(__name__)

from enum import Enum
Text = Enum('Text',
            'DecimalPoint AND MINUTE MINUTES SECONDS' +
            ' ERROR Intent_Error DuckDuckGo_ERROR' +
            ' Timer_Response GetTime_Response')
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
    Text.ERROR: "something went wrong  the message was {MESSAGE}",
    Text.Intent_Error: "i cannot find intent {INTENT}",
    Text.DuckDuckGo_ERROR: "no information found for {SEARCH}",
    Text.Timer_Response: "i set a timer for {MINUTES} {AND} {SECONDS}",
    Text.GetTime_Response: "the time is  {HOURS} hours and {MINUTES} minutes",
    
    DomoText.Error : "no answer received from domoticz",
    DomoText.GetWind_Response : "the wind is blowing {SPEED} meter per second from the {DIRECTION}",
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
    Text.ERROR: "Er is iets fout gegaan. de melding was {MESSAGE}",
    Text.DuckDuckGo_ERROR: "Geen informatie gevonden voor {SEARCH}",
    Text.Timer_Response: "ik heb een taimer gezet op {MINUTES} {AND} {SECONDS}",
    Text.GetTime_Response: "Het is nu  {HOURS}  uur en {MINUTES} minuten",

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
    PROFILEDIR = os.getenv("RHASSPY_PROFILE_DIR",default="en")
    return re.sub(".*/(..)$","\\1",PROFILEDIR)

def get_text(textid=Text.ERROR,textsubid=None):
    lang = get_language()
    default_lang = "en"
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
