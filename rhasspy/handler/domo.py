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

import datetime
import requests
import logging
import re
import json
log = logging.getLogger(__name__)
import traceback

class Domo:
    def __init__(self, url):
        self.url = url+"/json.htm?"

    def get_domoticz(self,command,firstOnly=True):
        url = self.url+command
        timeout=3.05
        log.debug(f"Url:{url}, timeout={timeout}")
        try:
            res = requests.get(url, timeout=(0.5, timeout))
            log.debug(f"request returned:({res})")
            if res.status_code != 200:
                log.info(f"Url:[{url}\nResult:{res.status_code}, text:{res.text}")
                return None
        except ConnectionError:
            log.warning(f"ConnectionError for {url}")
            return None

        except Timeout:
            log.warning(f"Timeout for {url}")
            return None
        except:
            log.warning("Unexpected error:", sys.exc_info()[0])
            return None

        log.debug(str(res))
        res_json = json.loads(res.text)
        log.debug(str(res_json))

        if "result" in res_json:
            if firstOnly:
                return(res_json["result"][0])
            return(res_json["result"])

        return(res_json)

    def getStringAsDate(self,date_string,date_format="%Y-%m-%d %H:%M:%S"):
        log.debug(f"getStringAsDate:date_string=[{date_string}], format=[{date_format}]")
        try :
            return datetime.datetime.strptime(date_string,date_format)
        except :
            return None

    def check_update(self, device, max_age_in_seconds):  # Default LastUpdate was less than 1800 sec. = 1/2 hour
        try :
            log.debug(f"max_age_in_seconds={max_age_in_seconds}")
            log.debug(f"device={device}")
            if max_age_in_seconds == 0 :
                return True

            if "LastUpdate" in device:
                now = datetime.datetime.now()
                lastupdate = self.getStringAsDate(device["LastUpdate"])
                seconds_past = (now - lastupdate).total_seconds()
                log.debug(f"seconds_past {seconds_past} > max_age_in_seconds {max_age_in_seconds} ? {seconds_past > max_age_in_seconds}")
                return seconds_past < max_age_in_seconds

            log.error(f"No LastUpdate field getting info for {field_name}")
            log.error(f"res_json:<<<{res_json}>>>")
            return False
        except :
            log.debug(f"{traceback.format_exc()}")
            return False  # Dirty programming!

    def get_info(self, idx=0,field_name=None,default="", max_age=0):
        try:
            log.debug(f"(idx={idx},field_name={field_name},max_age={max_age}")
            device = self.get_domoticz(f"type=devices&rid={idx}")
            log.debug(f"(device={device}")
            if not self.check_update(device, max_age) :
                return "OLD_DATA"
            if field_name is None:
                return device
            if field_name in device:
                return device[field_name]
            return default
        except :
            log.debug(f"{traceback.format_exc()}")
            return default  # Dirty programming!

    def set_scene(self,idx):
        command = f"type=command&param=switchscene&idx={idx}&switchcmd=On"
        self.get_domoticz(command)

    def set_switch(self,idx, state, level=-1):
        log.debug(f"set_switch(idx={idx},state={state},level={state}")
        if int(level) >= 0:
            maxDimLevel = self.get_info(idx,"MaxDimLevel","100")
            log.debug(f"(maxDimLevel={maxDimLevel})")
            level = int((level * int(maxDimLevel))/100 + 0.5)
            switchcmd = "Set Level&level=%d" % (level)
        else:
            switchcmd = state
        
        command = f"type=command&param=switchlight&idx={idx}&switchcmd={switchcmd}"
        self.get_domoticz(command)


    def get_devices(self,favorite=1):
        '''
            return list of devices containing selection of fields 
        '''
        devices = []
        res = self.get_domoticz(f"type=devices&filter=all&used=true&order=Name&favorite={favorite}",firstOnly=False)
        log.debug(f"res={res}")

        for device in res:
            log.debug(f"get_devices: dev={device}")
            if "idx" not in device:
                continue # Should never happen
            if 'Type' not in device:
                continue # Should never happen
            device_idx = int(device["idx"])
            device_type = device["Type"]

            if "LastUpdate" in device:
                lastupdate = device["LastUpdate"]
            else:
                lastupdate = ""

            if "SwitchType" in device:
                switch_type = device["SwitchType"]
            else:
                switch_type = ""

            if "SubType" in device:
                sub_type = device["SubType"]
            else:
                sub_type = ""

            if "Description" in device:
                device_desc = device["Description"]
            else:
                device_desc = ""

            if "Name" in device:
                device_name = device["Name"]
            else:
                device_name = ""

            dev_info = {"idx":device_idx,
                            "LastUpdate":lastupdate,
                            "Type":device_type,
                            "SwitchType":switch_type,
                            "SubType":sub_type,
                            "Name":device_name,
                            "Description":device_desc}
            devices.append(dev_info)
            log.debug(f"get_devices:added dev_info: {dev_info}.")

        return devices

    def get_devices_by_type(devType,subType="", favorite=1):
        '''
            return selection of devices of a Type/SubType (optional)
        '''
        devices = get_devices(self,favorite=1)
        selection = []
        for device in devices:
            if devType == device["Type"] and subType == device["SubType"]:
                selection.append(device)
                log.debug(f"get_device:added dev: {device}.")

        if len(devices) > 0:
            return devices[0]
        return None


# End Of File
