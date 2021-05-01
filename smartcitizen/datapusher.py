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

import re
import os
import sys
import rrdtool
import datetime
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


WEATHER = 1
P1 = 2

rrdfiledir_weather="/home/weather/data/"
rrdfiledir_p1="/home/weather/p1data/"

domo_host = "192.168.0.3"
domo_port = 8080

domo_idx_elektra = 6
domo_idx_gas = 7
domo_idx_temphum = 19
domo_idx_wind = 20

opt_verbose = 1

def get_lastdata(w_or_p1):
    data = { 'ds' : {'tempc':0,'windm':0,'winda':0,'windd':0,'humid':0,'rainmm':0,'current_elec_watt':0,'hourly_gas_liter':0},
            'date': 'NO DATA'}
    filename = datetime.datetime.now().strftime("%Y%m%d.rrd")
    if w_or_p1 == WEATHER:
        filename = rrdfiledir_weather+filename
        if opt_verbose >1 :
            print(f"Opening file {filename} ({w_or_p1})")
        # ds : tempc:windm:winda:windd:humid:rainmm",
    elif w_or_p1 == P1:
        filename = rrdfiledir_p1 + filename
        if opt_verbose >1 :
            print(f"Opening file {filename} ({w_or_p1})")
        #DS: current_elec_watt: hourly_gas_liter
        
    if os.path.exists(filename):
        data = rrdtool.lastupdate(filename)
        if opt_verbose >1:
            print(f"Date:{data['date']}\nDS:{str(data['ds'])}")
            #['tempc']}"
            #    +f"{int(3.6 * data['ds']['windm'])} km/u\n{data['ds']['humid']} %")
    return data

def send_url(url):
    log.debug(f"Url:{url}.")
        
    try:
        res = requests.get(url)
        if res.status_code != 200:
            log.info(f"Url:[{url}]")
            log.info(f"Result:{res.status_code}, text:{res.text}")
    except ConnectionError:
        timestamp = datetime.datetime.now().strftime("%Y%m%d %H:%M")
        log.error(f"ConnectionError for url {url} at {timestamp}")
'''
=====================
Gas
=====================
URL: /json.htm?type=command&param=udevice&idx=IDX&nvalue=0&svalue=USAGE
USAGE= Gas usage in liter (1000 liter = 1 m³)
So if your gas meter shows f.i. 145,332 m³ you should send 145332.
The USAGE is the total usage in liters from start, not f.i. the daily usage.
'''
def send_verbruik_gas(usage):
    get_url = f"http://{domo_host}:{domo_port}/json.htm?type=command&param=udevice&idx={domo_idx_gas}&svalue={usage}"
    send_url(get_url)
    

'''
=====================
Electricity (instant and counter)
=====================
URL: /json.htm?type=command&param=udevice&idx=IDX&nvalue=0&svalue=POWER;ENERGY
IDX = id of your device (This number can be found in the devices tab in the column "IDX")
POWER = current power
ENERGY = cumulative energy in Watt-hours (Wh) This is an incrementing counter. (if you choose as type "Energy read : Computed", this is just a "dummy" counter, not updatable because it's the result of DomoticZ calculs from POWER)
'''
def send_elektra(power,energy=0):

    get_url = f"http://{domo_host}:{domo_port}/json.htm?type=command&param=udevice&idx={domo_idx_elektra}&svalue={power};{energy}"
    send_url(get_url)

'''
=====================
Temperature/humidity
=====================
URL: /json.htm?type=command&param=udevice&idx=IDX&nvalue=0&svalue=TEMP;HUM;HUM_STAT
IDX = id of your device (This number can be found in the devices tab in the column "IDX")
TEMP = Temperature
HUM = Humidity (0-100 %)
HUM_STAT = Humidity status

HUM_STAT can be one of:
0=Normal
1=Comfortable
2=Dry
3=Wet
'''
def send_temp_hum(temp,hum,hum_stat=0):

    get_url = f"http://{domo_host}:{domo_port}/json.htm?type=command&param=udevice&idx={domo_idx_temphum}&svalue={temp};{hum};{hum_stat}"
    send_url(get_url)

'''
=====================
Wind
=====================
URL: /json.htm?type=command&param=udevice&idx=IDX&nvalue=0&svalue=WB;WD;WS;WG;22;24
IDX = id of your device (This number can be found in the devices tab in the column "IDX")
WB = Wind bearing (0-359)
WD = Wind direction (S, SW, NNW, etc.)
WS = 10 * Wind speed [m/s]
WG = 10 * Gust [m/s]
22 = Temperature
24 = Temperature Windchill
'''
windDirection =  ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
def winddir(bearing):
    return windDirection[int((float(bearing)+11.25)/22.5)]
    
def send_wind(wb,wd,ws,wg,temp,temp_wc=0):

    get_url = f"http://{domo_host}:{domo_port}/json.htm?type=command&param=udevice&idx={domo_idx_wind}&svalue={wb};{wd};{ws};{wg};{temp};{temp_wc}"
    send_url(get_url)

def send_weather():
    data = get_lastdata(WEATHER)
    if data['date'] != 'NO DATA':
        ds = data['ds']
        #send_wind(ds['windd'],winddir(ds['windd']),ds['winda'],ds['windm'],ds['tempc'])
        send_wind(ds['windd'],winddir(ds['windd']),str(int(10*float(ds['winda']))),str(int(10*float(ds['windm']))),ds['tempc'])
        send_temp_hum(ds['tempc'],ds['humid'])
        
def send_p1():
    data = get_lastdata(P1)
    if data['date'] != 'NO DATA':
        ds = data['ds']
        send_elektra(ds['current_elec_watt'])
        send_verbruik_gas(ds['hourly_gas_liter']/10000)

if __name__ == '__main__':
    formatstr = '%(asctime)s %(levelname)-5.5s %(module)-14.14s (%(lineno)d)'\
                 + '- %(message)s'
    logging.basicConfig(filename=PATH+'datapusher.log',
                        level=logging.DEBUG,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')

    while True:
        try:
            log.debug(f"new iteration")
            send_weather()
            send_p1()
            sleep(5)
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            debug.warn(f"ERROR:{e}, sleep for 5 minutes",file=sys.stderr)
            sleep(300)


