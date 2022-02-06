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
import logging

log = logging.getLogger(__name__)

# =============================================================================
# Conversations/Confirmation/Update Slots using rhasspy api
# =============================================================================
class Rhasspy:
    HEADERS_JSON = {"Content-Type": "application/json"}
    HEADERS_TEXT = {"Content-Type": "text/plain"}

    def __init__(self, url):
        self.url = url+"/api/"

    def do_post_rhasspy(self, url, data="", headers=HEADERS_TEXT):
        log.debug(f"Post data to rhasspy. url:{url}, data=[{data[:100]}], headers={headers}")
        try:
            res = requests.post(url, data=data.encode("utf-8"), headers=headers)
            if res.status_code != 200:
                log.info(f"do_post(Url:[{url}]\n"+
                    f"Result:{res.status_code}, text:[{res}]")
        except ConnectionError:
            log.warning(f"ConnectionError for url [{url}]")
            return None

        if log.isEnabledFor(logging.DEBUG):
            # check for header: content-type: audio/wav 
            if 'content-type' in res.headers:
                content_type = res.headers['content-type']
            if content_type == 'audio/wav':
                log.debug(f"Post Result:audio")
            else:
                log.debug(f"Post Result:{res.text}")
        return(res)


    def rhasspy_speak(self,question):
        self.do_post_rhasspy(self.url+"text-to-speech",question)


    def rhasspy_listen_for_intent(self):
        res = self.do_post_rhasspy(self.url+"listen-for-command?nohass=true")
        return res.json()


    def rhasspy_confirm(self,question):
        self.rhasspy_speak(question)
        res = self.rhasspy_listen_for_intent()
        log.debug(f"Reply={str(res)}")
        return("intent" in res and res["intent"]["name"] == "Confirm")


    '''
        To create slots (files) we use the Rhasspy API
        The data to post is formatted in JSON like this:
        {"slotname":["(speech):slotvalue", "(speech):slotvalue", "speech_slotvalue", ...}
        We create/update the slots for slotname with the list of slot entries
        DO NOT FORGET TO TRAIN!
    '''
    def rhasspy_add_slots(self,slots):
        self.do_post_rhasspy(self.url+"slots?overwriteAll=false",slots, Rhasspy.HEADERS_JSON)


    def rhasspy_replace_slots(self,slots):
        log.info(f"Slots=<{slots[:100]}>")
        self.do_post_rhasspy(self.url+"slots?overwriteAll=true",slots, Rhasspy.HEADERS_JSON)


    def rhasspy_train(self):
        self.do_post_rhasspy(self.url+"train")

    def rhasspy_restart(self):
        self.do_post_rhasspy(self.url+"restart")


# End Of File
