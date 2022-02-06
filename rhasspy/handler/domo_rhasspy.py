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
import json
import re

from domo import Domo
from rhasspy import Rhasspy
log = logging.getLogger(__name__)

class Domo_Rhasspy:

    def __init__(self, domo, rhasspy):
        self.domo = domo
        self.rhasspy = rhasspy


    '''
        Add to dict adds a speech to a list of entries
        If the speech already exists (we already have a filter defined)
        We check for:
        new is part of old: use new
        old is part of new: use old
        
    '''
    def add_to_dict(self,slot_entries,new_speech,new_filter):
        if new_speech in slot_entries:
            old_filter = slot_entries[new_speech]
            if new_filter in old_filter:
                my_filter = new_filter
            elif old_filter in new_filter:
                my_filter = old_filter
            else: # TODO Check the code
                my_filter = old_filter
                while not new_filter.startswith(old_filter):
                    old_filter = old_filter[:-1]
        else:
            my_filter = new_filter
            
        slot_entries[new_speech] = my_filter

    def dump(self,data):
        if type(data) is str:
            jdata = json.loads(data)
        elif type(data) is dict:
            jdata = data
        else:
            log.error(f"dump is called with wrong type: {type(data)}")
            return
        for slotname, slots in jdata.items():
            fslots = open(slotname, "w+")
            for line in slots:
                fslots.write(line+'\n')
            fslots.close()

    def save_slots(self,slots_dict,slotname):
        slots = []
        for speech,idx in sorted(slots_dict.items()):
            slots.append(f"({speech}):({idx})")
        slots_dict = { slotname :  slots }
        log.debug(f"Send to Rhasspy:<<<<{json.dumps(slots_dict)}>>>>")
        self.rhasspy.rhasspy_replace_slots(json.dumps(slots_dict))

    def clean_speech(self,slot_entry):
        cleaned = slot_entry.lower()
        # skip everyting before -
        cleaned = re.sub('^[^-]*-','',cleaned)
        cleaned = re.sub('[^a-z0-9 |]','',cleaned)
        cleaned = cleaned.strip()
        log.debug(f"clean_speech:<{slot_entry}> clean:<{cleaned}>")

        return cleaned

    def create_slots_switches(self):
        device_slots = {}
        devices = self.domo.get_devices_by_type("Light/Switch")
        for device in devices:
            if device["Description"] != "":
                speech_device = device["Description"]
            else:
                speech_device = device["Name"]

            self.add_to_dict(device_slots,self.clean_speech(speech_device),device["idx"])

        self.save_slots(device_slots,"switches")

    def create_slots_scenes(self,devices):
        device_slots = {}
        devices = self.domo.get_devices_by_type("Scene")
        for device in devices:
            if device["Description"] != "":
                speech_device = device["Description"]
            else:
                speech_device = device["Name"]

            self.add_to_dict(device_slots,self.clean_speech(speech_device),device["idx"])

        self.save_slots(device_slots,"scenes")

    def create_slots_files(self):
        self.create_slots_switches(devices)
        self.create_slots_scenes(devices)
        res = self.rhasspy.rhasspy_train()
        if res and res.status_code != 200:
            return res.text
        res = self.rhasspy.rhasspy_restart()
        return None


if __name__ == '__main__':

    logging.basicConfig(filename='domo_rhasspy.log',
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-4.4s %(module)-14.14s - %(message)s',
                        datefmt='%Y%m%d %H:%M:%S')

# End Of File
