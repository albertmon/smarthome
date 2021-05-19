#!/usr/bin/env python

config = {
    "urls" : 
        { "Rhasspy" : "http://localhost:12101"
        , "DuckDuckGo" : "https://api.duckduckgo.com"
        , "Domo" : "http://domopi:8080"
        , "Kodi" : "http://kodipi:8080"
        , "SmartCity" : "https://api.smartcitizen.me"
        }
    }

import os
import re
import logging
log = logging.getLogger(__name__)


def get_language():
    PROFILEDIR = os.getenv("RHASSPY_PROFILE_DIR",default="en")
    log.debug(f"PROFILEDIR={PROFILEDIR}.")
    lang = re.sub(".*/(..)$","\\1",PROFILEDIR)
    return lang + "-" + lang

def get_url(key):
    return config["urls"][key]

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
