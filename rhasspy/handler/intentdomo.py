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

import json
import requests
import intentconfig
from intentexcept import error_missing_parameter

import logging
log = logging.getLogger(__name__)

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
        log.debug(str(res_json))

        if "result" in res_json:
            return(res_json["result"][0])

        return(res_json)

    def domoInfo(self, idx,field_name,default=""):
        res_json = self.get_domoticz(f"type=devices&rid={idx}")
        if field_name in res_json:
            return res_json[field_name]
        return default

    def doDomoInfo(self):
        # get slots
        field_name = self.intentjson.get_slot_value("name", "Data")
        idx = self.intentjson.get_slot_value("idx")
        if not idx:
            error_missing_parameter("idx","DomoInfo")
        speech = self.intentjson.get_slot_value("speech")
        if not speech:
            error_missing_parameter("speech","DomoInfo")
        resultMatch = self.intentjson.get_slot_value("result","RESULT")

        # perform action
        value = self.domoInfo(idx,field_name)
        if value == "":
            # No value received, return Error result 
            log.warning(f"Error returned for idx:{idx}, fieldname:{field_name}."\
                + f"\n-----json--------\n{res_json}\n-----end json--------\n")
            speech = intentconfig.get_text(intentconfig.DomoText.Error)
            self.intentjson.set_speech(speech)
        else:
            # format speech result
            returnValue = intentconfig.replace_decimal_point(str(value))
            self.intentjson.set_speech(speech.replace(resultMatch,returnValue))


    def doDomoScene(self):
        # get slots
        idx = self.intentjson.get_slot_value("idx")
        if not idx:
            error_missing_parameter("idx","DomoScene")

        # format speech result
        speech = self.intentjson.get_slot_value("speech")
        if not speech:
            error_missing_parameter("speech","DomoScene")
        self.intentjson.set_speech(speech)

        # perform action
        command = f"type=command&param=switchscene&idx={idx}&switchcmd=On"
        self.get_domoticz(command)

    def doDomoDimmer(self):
        # get slots
        idx = self.intentjson.get_slot_value("idx")
        if not idx:
            error_missing_parameter("idx","DomoDimmer")
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
        if not idx:
            error_missing_parameter("idx","DomoSwitch")
        state = self.intentjson.get_slot_value("state")
        if not state:
            error_missing_parameter("state","DomoSwitch")
        log.debug(f"doDomoSwitch:idx={idx},state={state}")

        # perform action
        command = f"type=command&param=switchlight&idx={idx}&switchcmd={state}"
        log.debug(f"doDomoSwitch:command={command}")
        self.get_domoticz(command)

    def doDomoGetWind(self):
        idx = self.intentjson.get_slot_value("idx")
        if not idx:
            error_missing_parameter("idx","DomoGetWind")
        log.debug(f"doDomoGetWind:idx={idx}")

        # perform action
        command = f"type=devices&rid={idx}"
        log.debug(f"doDomoGetWind:command={command}")
        res_json = self.get_domoticz(command)

        if "Speed" and "DirectionStr" in res_json:   # json result is Ok
            speed = res_json["Speed"]
            direction = res_json["DirectionStr"]
            log.debug(f"Received: {speed},{direction}")
            speed = intentconfig.replace_decimal_point(speed)
            speech = intentconfig.get_text(intentconfig.DomoText.GetWind_Response)
            direction = intentconfig.get_text(intentconfig.DomoText.GetWind_Direction, direction)
            self.intentjson.set_speech(speech.format(SPEED=speed, DIRECTION=direction))
        else:
            log.warning(f"Error returned for idx:{idx}, fieldname:{field_name}."\
                + f"\n-----json--------\n{res_json}\n-----end json--------\n")
            speech = intentconfig.get_text(intentconfig.DomoText.Error)
            self.intentjson.set_speech(speech)

    def get_json_value(self, res_json, name, default=""):
        if name in res_json:
            return res_json[name]
        return default


    def doDomoSun(self):
        '''
            Return the data for dusk, sunrise, sunset and dawn.
            Data is retrieved from domoticz.
            Example JSON return:
                {
                  "ActTime": 1623943842,
                  "AstrTwilightEnd": "00:00",
                  "AstrTwilightStart": "00:00",
                  "CivTwilightEnd": "22:55",
                  "CivTwilightStart": "04:28",
                  "DayLength": "16:48",
                  "NautTwilightEnd": "00:16",
                  "NautTwilightStart": "03:06",
                  "ServerTime": "2021-06-17 17:30:42",
                  "SunAtSouth": "13:41",
                  "Sunrise": "05:17",
                  "Sunset": "22:05",
                  "app_version": "2020.2",
                  "status": "OK",
                  "title": "Devices"
                }
            The result is returned in tags DAWN, SUNRISE, SUNSET and DUSK
            in the speech slot
        '''
        # get slots
        speech = self.intentjson.get_slot_value("speech")
        if not speech:
            error_missing_parameter("speech","DomoSun")

        # perform action
        res_json = self.get_domoticz("type=devices&rid=0")
        log.debug(str(res_json))
        
        dawn = self.get_json_value(res_json,"CivTwilightStart").replace(':',' ')
        sunrise = self.get_json_value(res_json,"Sunrise").replace(':',' ')
        sunset = self.get_json_value(res_json,"Sunset").replace(':',' ')
        dusk = self.get_json_value(res_json,"CivTwilightEnd").replace(':',' ')

        # format speech result
        if "DAWN" in speech:
            speech = speech.replace('DAWN', dawn)
        log.debug(f"Speech(DAWN={dawn}: <{speech}>")
        if "SUNRISE" in speech:
            speech = speech.replace('SUNRISE', sunrise)
        if "SUNSET" in speech:
            speech = speech.replace('SUNSET', sunset)
        if "DUSK" in speech:
            speech = speech.replace('DUSK', dusk)
        log.debug(f"Speech(DUSK={dusk}: <{speech}>")

        self.intentjson.set_speech(speech)



