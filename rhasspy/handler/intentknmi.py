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

from domo import Domo
from rhasspy import Rhasspy
from domo_rhasspy import Domo_Rhasspy

import json
import random
import re
import requests
import intentconfig
from intentexcept import error_missing_parameter

import logging
log = logging.getLogger(__name__)

class Rain:

    def __init__(self, latitude, longitude):
        self.url_rain = "http://arduino.reshift.nl/nu.php"
        randNumber = random.randint(1,999999)
        self.rain_host_params = f"/data/raintext/?lat={latitude:.2f}&lon={longitude:.2f}&{randNumber}";
        # Vervang lat en lon door de gewenste coordinaten met twee decimalen.

    def get_http(self, url):
        log.debug(f"get data(url={url}")
        try:
            res = requests.get(url)
            if res.status_code != 200:
                log.info(f"do_get(Url:{url}\nResult:{res.status_code}, text:{res.text}")
        except ConnectionError:
            log.warning(f"ConnectionError for url [{url}]")
            return None

        log.debug("Get Result:"+res.text)
        return(res.text)

    def get_tag(self, text, begin_tag, einde_tag):
        log.debug(f"text, begin_tag, einde_tag: {text}, {begin_tag}, {einde_tag}")
        result = ""
        last = re.sub(f".*{begin_tag}(.*)","\\1",text)
        log.debug(f"last: {last}")
        if (len(last) < len(text)):
            result = re.sub(f"{einde_tag}.*","",last)
        log.debug(f"begin={begin_tag}, end={einde_tag}.\ntext=<<<{text}>>>\nresult=<<<{result}>>>")
        return result

    RAIN_EXPECTED_DATA_ERROR       = -1
    RAIN_EXPECTED_PERIOD_TOO_SHORT = -2

    def get_rain_data(self):
        response = self.get_http(self.url_rain)
        time_now = self.get_tag(response,"<tijdstip>","</tijdstip>")
        log.debug(f"Huidig tijdstip: {time_now}");
        if not time_now :
            return ("unknown", None)

        rain_host = self.get_tag(response,"<regen>","</regen>")
        log.debug("rain_host="+rain_host)
        raindata = self.get_http(f"http://{rain_host}{self.rain_host_params}")
        return (time_now, raindata)

    def get_total_rain(self, time_now, rainlist, minutes):
        # calculate max index in rainlist to calculate rain forecast in mm
        # rainlist contains entries per 5 minutes, starting with header
        log.debug(f"time_now={time_now}, rainlist={rainlist}, minutes={minutes}")
        MINIMUM_PERIOD = 3 # Minimal period is 15 minutes
        max_range = int(minutes/5) + 1
        max_range = min(max(max_range,MINIMUM_PERIOD),min(max_range,len(rainlist)))
        if max_range < MINIMUM_PERIOD:
            return (self.RAIN_EXPECTED_PERIOD_TOO_SHORT, None, None)
        now_in_list = False
        first_time = None
        last_time = None
        total_rain_expected = 0
        i = 1
        while i < max_range:
            data = rainlist[i].split("|")
            log.debug(f"({i}) {data}, total_rain_expected={total_rain_expected}, max_range={max_range}")
            if time_now in data[1]:
                first_time = data[1]
            now_in_list = now_in_list or time_now in data[1] # are we checking the right data?
            try: 
                rainvalue = int(data[0])
            except ValueError:
                rainvalue = 0

            if now_in_list and rainvalue > 0 :
                # translate rainfall value (0-999) to mm in this period (5 minutes)
                log.debug(f"({i})rainvalue={rainvalue}")
                mm_in_period = rainvalue / 120  # .9 mm/hr = 009, 12 periods per hour
                total_rain_expected = total_rain_expected + mm_in_period
                last_time = data[1]
            elif not now_in_list:
                # we skip until we found now in list or we reach the end of the data
                max_range = min(max_range+1,len(rainlist))
            i += 1

        if now_in_list:
            if total_rain_expected > 0 and total_rain_expected < 1:
                total_rain_expected = .9
            return (int(total_rain_expected+0.5), first_time, last_time)

        log.error(f"current time {time_now} (as received from {self.url_rain}) not found in result")
        return (self.RAIN_EXPECTED_DATA_ERROR, None, None)


    def get_rainforecast(self, minutes=60):
        log.debug(f"args(minutes={minutes})")
        (time_now, raindata) = self.get_rain_data()
        log.debug(f"time_now={time_now}")
        if raindata is None:
            log.error(f"No data received from {self.url_rain}")
            return self.RAIN_EXPECTED_DATA_ERROR

        rain_array = raindata.split("\r")
        if len(rain_array) == 1:
            log.error(f"Unexpected answer from rain host:<{rain_array[0]}>")
            return self.RAIN_EXPECTED_DATA_ERROR

        rain_array.pop()  # Remove last (empty) entry
        (total_rain, first_time, last_time) = self.get_total_rain(time_now, rain_array, minutes)

        log.debug(f"checkrain end, total_rain={total_rain}")
        return total_rain

class IntentKNMI:
    '''
    Class IntentKNMI implements intents for KNMI-api weather info
    The info is received from: https://weerlive.nl/api/json-data-10min.php?key=demo&locatie=Amsterdam
    Summary of the result-data
        plaats	de locatie
        temp	actuele temperatuur
        gtemp	gevoelstemperatuur
        samenv	omschrijving weersgesteldheid
        lv	relatieve luchtvochtigheid
        windr	windrichting
        windms	windsnelheid in meter per seconde
        winds	windkracht (Beaufort)
        luchtd	luchtdruk (hPa)
        dauwp	dauwpunt
        zicht	zicht in km
        verw	korte dagverwachting
        d0tmax	Maxtemp vandaag
        d0tmin	Mintemp vandaag
        d0windk	Windkracht vandaag (in Bft)
        d0windr	Windrichting vandaag
        d0neerslag  Neerslagkans vandaag (%)
        d0zon	Zonkans vandaag (%)
        d1weer	Weericoon morgen
        d1tmax	Maxtemp morgen
        d1tmin	Mintemp morgen
        d1windk	Windkracht morgen (in Bft)
        d1windr	Windrichting morgen
        d1neerslag	Neerslagkans morgen (%)
        d1zon	Zonkans morgen (%)
        alarm	Geldt er een weerwaarschuwing voor deze regio of niet?
        alarmtxt	Als er sprake is van een waarschuwing, verschijnt alarmtxt in de API. Hier lees je de omschrijving van de weersituatie.
    
    All intents accept the parameters:
        speech (optional, default depending intent)- text to speak after executing the intent
        apikey (optional) - API-key for KNMI. If not present, only data for Amsterdam is given
        location (optional) - 
        info - 

    Implemented Intents are:
    KNMIInfo - Return spoken information from KNMI
        Parameters:
    KNMIGetWind - Special info intent to hear the wind speed and direction
        Parameter:
    '''

    def __init__(self, intentjson):
        self.intentjson = intentjson
        self.knmi_url = intentconfig.get_url("KNMI")

    def get_info(self, key="demo", location="Amsterdam"):
        url = f"{self.knmi_url}?key={key}&locatie={location}"
        log.debug(f"get data(url={self.knmi_url}?key={key}&locatie={location}")
        try:
            res = requests.get(url)
            if res.status_code != 200:
                log.info(f"do_get(Url:{url}\nResult:{res.status_code}, text:{res.text}")
        except ConnectionError:
            log.warning(f"ConnectionError for url [{url}]")
            return None

        log.debug("Get Result:"+res.text)
        return(res.json())

    def get_json_value(self, res_json, name, default=""):
        if name in res_json:
            return res_json[name]
        return default

    def doKNMIInfo(self):
        # get slots
        key = self.intentjson.get_slot_value("location", "demo")
        location = self.intentjson.get_slot_value("location", "Amsterdam")
        speech = self.intentjson.get_slot_value("speech")
        log.debug(f"key={key},location={location},speech={speech}")
        resultMatch = self.intentjson.get_slot_value("result","VERW")

        # perform action
        info = self.get_info(key, location)
        if resultMatch.lower() in info:
            # format speech result
            returnValue = intentconfig.replace_decimal_point(info[resultMatch.lower()])
            self.intentjson.set_speech(speech.replace(resultMatch,returnValue))
        else:
            # No value received, return Error result 
            log.warning(f"Error returned for fieldname:{resultMatch}."\
                + f"\n-----json--------\n{res_json}\n-----end json--------\n")
            speech = intentconfig.get_text(intentconfig.DomoText.Error)
            self.intentjson.set_speech(speech)

    def winddir(self,bearing):
        windDirection =  ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
        return windDirection[int((float(bearing)+11.25)/22.5)]


    def doKNMIGetWind(self):
        # get slots
        key = self.intentjson.get_slot_value("key", "demo")
        location = self.intentjson.get_slot_value("location", "Amsterdam")
        speech = self.intentjson.get_slot_value("speech")
        log.debug(f"key={key},location={location},speech={speech}")

        # perform action
        res_json = self.get_info(key, location)
        # windr:  windrichting
        # windrgr: bearing (windrichting in graden)
        # windms: windsnelheid in meter per seconde
        # winds:  windkracht (Beaufort)

        res = res_json["liveweer"][0]
        log.debug(f"Received: {res}")
        if "windms" and "windrgr" and "winds" in res:   # json result is Ok
            speed = res["windms"]
            bearing = res["windrgr"]
            log.debug(f"Bearing: {bearing}")
            log.debug(f"Bearingflt: {float(bearing)}")
            log.debug(f"Bearingint: {int((float(bearing)+11.25)/22.5)}")
            direction = self.winddir(bearing)
            log.debug(f"direction: {direction}")
            beaufort = res["winds"]
            log.debug(f"Received: {speed},{direction}, {beaufort}")
            speed = f"in {location} " + intentconfig.replace_decimal_point(speed)
            log.debug(f"speed: {speed}")
            speech = intentconfig.get_text(intentconfig.DomoText.GetWind_Response)
            log.debug(f"Speech: {speech}")
            direction = intentconfig.get_text(intentconfig.DomoText.GetWind_Direction, direction)
            speech = speech.format(SPEED=speed, DIRECTION=direction, BEAUFORT=beaufort,BEAUFORT_TEXT="")
            log.debug(f"Speech: {speech}")
            self.intentjson.set_speech(speech)
        else:
            log.error(f"Error returned for key:{key}, location:{location}."\
                + f"\n-----json--------\n{res_json}\n-----end json--------\n")
            speech = intentconfig.get_text(intentconfig.Text.ERROR)
            self.intentjson.set_speech(speech)

    def doKNMIGetRain(self):
        # get slots lat=52.66&lon=4.82
        lat = self.intentjson.get_slot_value("lat", "52.66")
        lon = self.intentjson.get_slot_value("lon", "4.82")
        speech = self.intentjson.get_slot_value("speech")
        log.debug(f"lat={lat},lon={lon},speech={speech}")
        rain = Rain(float(lat),float(lon))
        log.debug(f"rain.rain_host_params={rain.rain_host_params}")
        rain_forecast = rain.get_rainforecast(minutes=60)
        if rain_forecast < 0 :  # Something went wrong
            log.debug(f"rain_forecast={rain_forecast}")
            speech = intentconfig.get_text(intentconfig.Text.ERROR)
        else:
            log.debug(f"rain_forecast={rain_forecast}")
            forecast = str(rain_forecast)
            speech = speech.replace('RESULT', forecast)
            log.debug(f"Speech after replace RESULT={forecast} : {speech}")

        self.intentjson.set_speech(speech)


# End Of File