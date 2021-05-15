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

# import sys
import json
# import datetime
import requests
# import subprocess

# from intentjson import IntentJSON
# from intentkodi import IntentKodi
# from rhasspy import Rhasspy
# from kodi import Kodi
import intentconfig

import logging
log = logging.getLogger(__name__)

PATH = "/profiles/nl/handler/"

class IntentDomo:
    '''
    Class IntentDomo implements intents for Domoticz
    All intents accept the parameter:
        speech (optional, default depending intent)
            - text to speak after executing the intent

    Implemented Intents are:
    DomoInfo - Return spoken information from a sensor
        Parameters:
            idx (required)- Device idx from Domoticz
            name (optional, Default "Data")
                - Name of the field of the sensordata that must be retrieved 
            speech - text to speak with the result, see parameter result
            result (optional, default RESULT)
                - string to replace in speech with result
    DomoScene - Start a Scene
        Parameter:
            idx (required)- Scene idx from Domoticz
    DomoDimmer - Set dimmer to a certain percentage level (0-100%)
        Parameters:
            idx (required)- Device idx from Domoticz
            level (optional, default 100%)
                - light level to set to, must be integer between 0 and 100
    DomoSwitch - Put something On or Off
        Parameters:
            idx (required)- Device idx from Domoticz
            state (required) - Must contain 'On' or 'Off'
                You can use (..:On|..:Off){state} to get the right value in sentences.ini
    DomoGetWind - Special info intent to hear the wind speed and direction
        Parameter:
            idx (required)- Device idx from Domoticz
    '''
    wind = {"N": "noord",
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

    def __init__(self, intentjson):
        domoticz_url = intentconfig.get_url("Domo")+"/json.htm?"
        self.domoticz_url = domoticz_url
        self.intentjson = intentjson

    def get_domoticz(self,command):
        url = self.domoticz_url+command
        log.debug("Url:"+url)
        try:
            res = requests.get(url)
            if res.status_code != 200:
                log.info(f"Url:[{url}\nResult:{res.status_code}, text:{res.text}")
                return None
        except ConnectionError:
            log.warning(f"ConnectionError for {url}")
            return None

        log.debug(str(res))
        res_json = json.loads(res.text)

        if "result" in res_json:
            return(res_json["result"][0])

        return(None)
        
    def domoInfo(self, idx, field_name="Data", defaultValue=""):
        res_json = self.get_domoticz(f"type=devices&rid={idx}")
        log.debug("Domoticz result: "+str(res_json))
        if field_name in res_json:
            value = res_json[field_name]
        else:
            value = defaultValue
        return (value)

    def doDomoInfo(self):
        # get slots
        field_name = self.intentjson.get_slot_value("name", "Data")
        idx = self.intentjson.get_slot_value("idx")
        resultString = self.intentjson.get_slot_value("speech")
        resultMatch = self.intentjson.get_slot_value("result","RESULT")

        # perform action
        value = self.domoInfo(idx, field_name,"geen idee")

        # format speech result
        returnValue = str(value).replace("."," komma ")
        self.intentjson.set_speech(resultString.replace(resultMatch,returnValue))

    def doDomoScene(self):
        # get slots
        idx = self.intentjson.get_slot_value("idx")

        # format speech result
        self.intentjson.set_speech(self.intentjson.get_slot_value("speech"))

        # perform action
        command = f"type=command&param=switchscene&idx={idx}&switchcmd=On"
        self.get_domoticz(command)

    def doDomoDimmer(self):
        # get slots
        idx = self.intentjson.get_slot_value("idx", default=-1)
        state = self.intentjson.get_slot_value("state",default="Off")
        level = self.intentjson.get_slot_value("level", default=100)

        # perform action
        log.debug(f"doDomoDimmer(idx={idx}, state={state}, level={level})")
        if level >= 0:
            maxDimLevel = self.domoInfo(idx,"MaxDimLevel","100")
            log.debug(f"(maxDimLevel={maxDimLevel})")
            level = int((level * int(maxDimLevel))/100 + 0.5)
            switchcmd = "Set Level&level=%d" % (level)
        else:
            switchcmd = state
        command = f"type=command&param=switchlight&idx={idx}&switchcmd={switchcmd}"
        self.get_domoticz(command)

    def doDomoSwitch(self):
        # get slots
        idx = self.intentjson.get_slot_value("idx")
        state = self.intentjson.get_slot_value("state")
        log.debug(f"doSwitch:idx={idx},state={state}")

        # perform action
        command = f"type=command&param=switchlight&idx={idx}&switchcmd={state}"
        log.debug(f"domoSwitch:command={command}")
        self.get_domoticz(command)

    def doDomoGetWind(self):
        idx = self.intentjson.get_slot_value("idx")
        log.debug(f"doDomoGetWind:idx={idx}")

        # perform action
        command = f"type=devices&rid={idx}"
        log.debug(f"doDomoGetWind:command={command}")
        res_json = self.get_domoticz(command)

        if "Speed" and "DirectionStr" in res_json:   # json result is Ok
            speed = res_json["Speed"]
            direction = res_json["DirectionStr"]
            log.debug(f"Received: {speed},{direction}")
            speed = speed.replace(".", " komma ")
            self.intentjson.set_speech(f"Het waait {speed} meter per seconde uit {IntentDomo.wind[direction]}elijke richting")
        else:
            self.intentjson.set_speech("Geen antwoord van domoticz ontvangen")


