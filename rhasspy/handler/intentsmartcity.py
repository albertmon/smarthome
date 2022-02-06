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

class IntentSmartCity:
    '''
    Class IntentSmartCity implements intents for Smart citizen

    Implemented Intents are:
    SmartCityInfo - Retrieve information from a smart citizen sensor
        Parameters:
            kit (required) - Kit number to retrieve from
            idx (required) - Device id from kit
            speech - text to speak with the result, see parameter result
            result (optional, default RESULT)
                - string to replace in speech with result
            novalue (optional, default "")
                - value to use when no result was received
    '''
    def __init__(self, intentjson):
        smartcitizen_url = intentconfig.get_url("SmartCity")
        self.smartcitizen_url = smartcitizen_url + "/v0/devices/"
        self.intentjson = intentjson

    def get_smartcitizen(self,kit):
        url = self.smartcitizen_url+kit
        log.debug("Url:"+url)
        try:
            res = requests.get(url)
            if res.status_code != 200:
                log.info(f"Url:[{url}\nResult:{res.status_code}, text:{res.text}")
                return None
        except ConnectionError:
            log.warning(f"ConnectionError for {url}")
            return None

        log.debug(str(res.text))
        res_json = json.loads(res.text)

        return(res_json)
        
    def smartCityInfo(self, kit, idx, defaultValue=""):
        res_json = self.get_smartcitizen(kit)
        log.debug("Smartcitizen result: "+str(res_json))
        value = defaultValue
        if res_json is not None and "data" in res_json\
           and "sensors" in res_json["data"]:
            sensors = res_json["data"]["sensors"]
            log.debug("Smartcitizen result sensors: "+str(sensors))
            for sensor in sensors:
                log.debug("Smartcitizen result: 1 sensor "+str(sensor))
                if "id" in sensor and sensor["id"] == idx:
                    if "value" in sensor:
                        value = sensor["value"]
                        break

        return (value)

    def doSmartCityInfo(self):
        # get slots
        kit = self.intentjson.get_slot_value("kit")
        if not kit:
            error_missing_parameter("kit","doSmartCityInfo")
        idx = self.intentjson.get_slot_intvalue("idx",0)
        if idx == 0:
            error_missing_parameter("idx","doSmartCityInfo")
        speech = self.intentjson.get_slot_value("speech")
        if not speech:
            error_missing_parameter("speech","doSmartCityInfo")
        defaultValue = self.intentjson.get_slot_value("novalue","")
        resultMatch = self.intentjson.get_slot_value("result","RESULT")
        log.debug("doSmartCityInfo:kit={kit}, idx={idx}.")
        # perform action
        value = self.smartCityInfo(kit, idx, defaultValue)
        log.debug("doSmartCityInfo:value={value}.")

        # format speech result
        returnValue = str(value).replace("."," komma ")
        result = speech.replace(resultMatch,returnValue)
        log.debug("doSmartCityInfo:result={result}.")
        self.intentjson.set_speech(result)

