#!/usr/bin/python3

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

import sys
import requests
from time import sleep
import logging

log = logging.getLogger(__name__)

# ====================================================================
# Begin of configurable data
# ====================================================================
# Path to the file with logging output
LOGFILE_PATH = 'datapusher.log'

# LOGLEVEL can be set to logging.DEBUG, logging.INFO, logging.WARN,
#          logging.ERROR or logging.CRITICAL
LOGLEVEL = logging.DEBUG

# URL to the devices you want to read
SMART_CITIZEN_URL = "https://api.smartcitizen.me/v0/devices/13371"

# URL to your Domoticz server
DOMOTICZ_URL = "http://192.168.0.3:8080"

'''
    SENSORS is a list of sensor mappings, to upload data to domoticz
    Format for sensors entry: 
    { "type" : ("Barometer" or "Lux". To be implemented later: "Air" etc"),
      "scid" : (id of smartcitizen sensor - check with json output),
      "domoidx" : (idx of the device in Domoticz)
    }
'''
#Temperature is implemented
SENSORS = [ {"type" : "Barometer", "scid" : 58, "domoidx": 25},
            {"type" : "Lux", "scid" : 14, "domoidx": 24},
            {"type" : "Temperature", "scid" : 55, "domoidx": 26} ]

# number of seconds before a timeout is reported
NO_DATA_TIMEOUT = 600
# seconds to wait for next data gathering
POLL_INTERVAL = 60

# ====================================================================
# End of configurable data
# ====================================================================


def api_get(url):
    log.debug(f"api_get(url={url})")

    try:
        res = requests.get(url)
        if res.status_code != 200:
            log.warn(f"api_get({url}), Result:{res.status_code}, text:{res.text}")
    except ConnectionError:
        log.warn(f"ConnectionError for url {url}")
        return(None)

    return res.json


# def send_baro(idx,value):
    # get_url = f"{DOMOTICZ_URL}/json.htm?type=command&param=udevice&idx={idx}"\
    # api_get(get_url)


# def send_lux(idx,value):
    # get_url = f"{DOMOTICZ_URL}/json.htm?type=command&param=udevice&idx={idx}"\
              # + f"{value}"
    # send_url(get_url)

def send_data(sensor,config):
    log.debug(f'send_data(sensor={str(sensor)})')
    log.debug(f'send_data(config={str(config)})')
    idx = config["domoidx"]
    get_url = f"{DOMOTICZ_URL}/json.htm?type=command&param=udevice&idx={idx}"
    if config["type"] == "Barometer":
        api_get(get_url+f'&nvalue=0&svalue={sensor["value"]*10};0')
    elif config["type"] == "Lux":
        api_get(get_url+f'&svalue={sensor["value"]}')
    elif config["type"] == "Temperature":
        api_get(get_url+f'&nvalue=0&svalue={sensor["value"]}')
        

def get_sensordata():
    log.debug("get sensordata from:"+SMART_CITIZEN_URL)
    try:
        res = requests.get(SMART_CITIZEN_URL)
        if res.status_code != 200:
            log.warn(f"get sensordata from: {SMART_CITIZEN_URL}], Result:{res.status_code}, text:{res.text}")
    except ConnectionError:
        timestamp = datetime.datetime.now().strftime("%Y%m%d %H:%M")
        log.warn(f"ConnectionError for url {SMART_CITIZEN_URL}")

    json_data = res.json()
    log.debug("json_data="+str(json_data))
    return(json_data["data"])


'''
		"sensors": [
			{
				"id": 113,
				"ancestry": "111",
				"name": "AMS CCS811 - TVOC",
				"description": "Total Volatile Organic Compounds Digital Indoor Sensor",
				"unit": "ppb",
				"created_at": "2019-03-21T16:43:37Z",
				"updated_at": "2019-03-21T16:43:37Z",
				"measurement_id": 47,
				"uuid": "0c2a1afc-dc08-4066-aacb-0bde6a3ae6f5",
				"value": 0.0,
				"raw_value": 0.0,
				"prev_value": 0.0,
				"prev_raw_value": 0.0
			},

'''


def send_sensors():
    data = get_sensordata()
    for sensor in data["sensors"]:
        log.debug("id:%s,name:%s, value:%d (%s)"
                  % (sensor["id"], sensor["name"],
                     sensor["value"], sensor["unit"]))
        for config in SENSORS:
            if sensor["id"] == config["scid"]:
                send_data(sensor, config)
                break


# ============================================================================

formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s (%(lineno)d)'\
             + '- %(message)s'
logging.basicConfig(filename=LOGFILE_PATH,
                    level=logging.DEBUG,
                    format=formatstr,
                    datefmt='%Y%m%d %H:%M:%S')

while True:
    try:
        print("new iteration")
        send_sensors()
        print("sleep "+str(POLL_INTERVAL))
        sleep(POLL_INTERVAL)
    except ConnectionError: # catch *all* exceptions
        log.error(f"{sys.exc_info()[0]}")


