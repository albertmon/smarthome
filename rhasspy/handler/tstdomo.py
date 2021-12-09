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
# from intentexcept import error_missing_parameter
import re
import logging
import intentconfig
from rhasspy import Rhasspy
from intentdomo import IntentDomo
from intentjson import IntentJSON
log = logging.getLogger(__name__)

# def get_domoticz(command,firstOnly=True):
    # url = domoticz_url+command
    # log.debug("Url:"+url)
    # try:
        # res = requests.get(url)
        # if res.status_code != 200:
            # log.debug(f"Url:[{url}\nResult:{res.status_code}, text:{res.text}")
            # return None
    # except ConnectionError:
        # log.warning(f"ConnectionError for {url}")
        # return None

    # log.debug(str(res))
    # res_json = json.loads(res.text)
    # log.debug(str(res_json))

    # if "result" in res_json:
        # if firstOnly:
            # return(res_json["result"][0])
        # return(res_json["result"])

    # return(res_json)


# Path to the file with logging output
LOGFILE_PATH = '/home/pi/Public/smarthome/rhasspy/handler/tstdomo.log'

# LOGLEVEL can be set to logging.DEBUG, logging.INFO, logging.WARN,
#          logging.ERROR or logging.CRITICAL
LOGLEVEL = logging.INFO

def replace_slots(slots):
    log.info(f"Slots=<{slots}>")
    for entry in slots:
        json_str = '{'+ '"'+entry+'":'+json.dumps(slots[entry])+'}'
        log.debug(f"json voor {entry} = >{json_str}<")
        rhasspy.rhasspy_replace_slots(json_str)
    rhasspy.rhasspy_train()

if __name__ == '__main__':

    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s'\
                 +' (%(lineno)d)- %(message)s'
    logging.basicConfig(filename=LOGFILE_PATH,
                        level=LOGLEVEL,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')

    rhasspy_url = "http://192.168.0.3:12101"
    rhasspy = Rhasspy(rhasspy_url)
    intentjson = IntentJSON("{}")
    intentdomo = IntentDomo(intentjson)
    log.debug("starting tst")
    domo_devices = intentdomo.get_domo_devices()
    slots = intentconfig.get_rhasspy_domo_slots(domo_devices)
    log.info(f"slots={slots}")
    replace_slots(slots)
    

# End of File
