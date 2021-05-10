#!/usr/bin/env python

config = {
    "urls" : 
        { "Rhasspy" : "http://192.168.0.3:12101"
        , "DuckDuckGo" : "https://api.duckduckgo.com"
        , "Domo" : "http://192.168.0.3:8080"
        , "Kodi" : "http://192.168.0.5:8080"
        }
    }
    
from intentdomo import IntentDomo
from intentkodi import IntentKodi

def get_url(key):
    return config["urls"][key]

def get_instances(json):
    instances = {}
    instances["Domo"] = IntentDomo(json)
    instances["Kodi"] = IntentKodi(json)
    return instances
