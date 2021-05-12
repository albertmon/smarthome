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
import intentconfig

log = logging.getLogger(__name__)

# =============================================================================
# Conversations/Confirmation using rhasspy api
# =============================================================================
class Rhasspy:
    def __init__(self, url):
        self.url = url+"/api/"

    def do_post_rhasspy(self, url, data=""):
        log.debug("Post data to rhasspy_url:"+data)
        try:
            res = requests.post(url, data=data)
            if res.status_code != 200:
                log.info("do_post(Url:[%s]\nResult:%s, text:[%s]"
                         % (url, res.status_code, res.text))
        except ConnectionError:
            log.warning("ConnectionError for url [%s]" % (url))
            return None

        # log.debug("Post Result:"+res.text)
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

