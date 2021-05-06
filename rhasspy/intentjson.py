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

import logging
log = logging.getLogger(__name__)

class IntentJSON:
    def __init__(self, json):
        self.jsonevent = json

    def get_json_as_string(self):
        return json.dumps(self.jsonevent)

    def get_intent(self):
        if "intent" in self.jsonevent and "name" in self.jsonevent["intent"]:
            return self.jsonevent["intent"]["name"]
        else:
            return ""
            
    def set_speech(self,text):
        log.debug("speech:"+text)
        self.jsonevent["speech"] = {"text": text}
        log.debug(str(self.jsonevent["speech"]))


    def get_slot_value(self,slot_name,default=""):
        if slot_name in self.jsonevent["slots"]:
            return self.jsonevent["slots"][slot_name]
        return default

    def get_raw_value_for(self,entity_name):
        for entity in self.jsonevent["entities"]:
            if entity["entity"] == entity_name:
                return entity["raw_value"]
        return ""

    def get_speech(self,text_to_speak):
        is_var = False
        new_speech = ""
        for text in text_to_speak.split('.'):
           if is_var:
               new_speech = new_speech + get_raw_value_for(text)
           else:
               new_speech = new_speech + text
           is_var = not is_var
        return new_speech

