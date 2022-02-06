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
import requests
import intentconfig
from intentexcept import error_missing_parameter

import logging
log = logging.getLogger(__name__)

class IntentDomo:
    '''
    Class IntentDomo implements intents for Domoticz
    All intents accept the parameter:
        speech (optional, default depending intent)
            - text to speak after executing the intent

    Implemented Intents are:
    DomoInfo - Return spoken information from a sensor
        Parameters:
            idx (required)- Device idx from Domoticz
            name (optional, Default "Data")
                - Name of the field of the sensordata that must be retrieved 
            speech - text to speak with the result, see parameter result
            result (optional, default RESULT)
                - string to replace in speech with result
    DomoScene - Start a Scene
        Parameter:
            idx (required)- Scene idx from Domoticz
    DomoDimmer - Set dimmer to a certain percentage level (0-100%)
        Parameters:
            idx (required)- Device idx from Domoticz
            level (optional, default 100%)
                - light level to set to, must be integer between 0 and 100
    DomoSwitch - Put something On or Off
        Parameters:
            idx (required)- Device idx from Domoticz
            state (required) - Must contain 'On' or 'Off'
                You can use (..:On|..:Off){state} to get the right value in sentences.ini
    DomoGetWind - Special info intent to hear the wind speed and direction
        Parameter:
            idx (required)- Device idx from Domoticz
    '''

    def __init__(self, intentjson):
        self.intentjson = intentjson
        domo_url = intentconfig.get_url("Domo")
        self.domo = Domo(domo_url)
        rhasspy_url = intentconfig.get_url("Rhasspy")
        self.rhasspy = Rhasspy(rhasspy_url)

    def doDomoScene(self):
        # get slots
        idx = self.intentjson.get_slot_intvalue("idx")
        if not idx:
            error_missing_parameter("idx","DomoScene")

        # perform action
        self.domo.set_scene(idx)

    def doDomoDimmer(self):
        # get slots
        idx = self.intentjson.get_slot_intvalue("idx")
        if not idx:
            error_missing_parameter("idx","DomoDimmer")
        state = self.intentjson.get_slot_value("state",default="Off")
        level = self.intentjson.get_slot_intvalue("level", default=100)

        # perform action
        log.debug(f"doDomoDimmer(idx={idx}, state={state}, level={level})")
        self.domo.set_switch(idx, state, level)

    def doDomoSwitch(self):
        # get slots
        idx = self.intentjson.get_slot_intvalue("idx")
        if not idx:
            error_missing_parameter("idx","DomoSwitch")
        state = self.intentjson.get_slot_value("state")
        if not state:
            error_missing_parameter("state","DomoSwitch")
        log.debug(f"doDomoSwitch:idx={idx},state={state}")

        # perform action
        self.domo.set_switch(idx,state)

    def doDomoInfo(self):
        # get slots
        field_name = self.intentjson.get_slot_value("name", "Data")
        max_age = self.intentjson.get_slot_intvalue("maxage", 0)
        
        idx = self.intentjson.get_slot_intvalue("idx")
        if not idx:
            error_missing_parameter("idx","DomoInfo")
        speech = self.intentjson.get_slot_value("speech")
        if not speech:
            error_missing_parameter("speech","DomoInfo")
        resultMatch = self.intentjson.get_slot_value("result","RESULT")
        log.debug(f"field_name={field_name},speech={speech},resultMatch={resultMatch}")

        # perform action
        info = self.domo.get_info(idx,max_age=1800)
        log.debug(f"idx={idx},max_age={max_age},info={info}")
        if info == "":
            # No info received, return Error result 
            log.warning(f"Error returned for idx:{idx}, fieldname:{field_name}."\
                + f"\n-----json--------\n{info}\n-----end json--------\n")
            speech = intentconfig.get_text(intentconfig.DomoText.Error)
            self.intentjson.set_speech(speech)
        elif info == "OLD_DATA":
            # LastUpdate too long ago 
            log.warning(f"Old returned for idx:{idx}, fieldname:{field_name}."\
                + f"\n-----json--------\n{info}\n-----end json--------\n")
            speech = intentconfig.get_text(intentconfig.DomoText.Old_data)
            self.intentjson.set_speech(speech)
        else:
            # format speech result
            returnValue = intentconfig.replace_decimal_point(str(info))
            self.intentjson.set_speech(speech.replace(resultMatch,returnValue))


    def doDomoGetWind(self):
        idx = self.intentjson.get_slot_intvalue("idx")
        if not idx:
            error_missing_parameter("idx","DomoGetWind")
        log.debug(f"doDomoGetWind:idx={idx}")

        # perform action
        res_json = self.domo.get_info(idx,max_age=1800)

        log.debug(f"Received: <{res_json}>")
        if str(res_json) == "OLD_DATA" :
            log.warning(f"Old data returned for idx:{idx}"\
                + f"\n-----json--------\n{res_json}\n-----end json--------\n")
            speech = "Geen informatie, de data is verouderd"
            self.intentjson.set_speech(speech)
            log.debug("x")
            return

        if "Speed" and "DirectionStr" in res_json:   # json result is Ok
            speed = res_json["Speed"]
            direction = res_json["DirectionStr"]
            log.debug(f"Received: {speed},{direction}")
            (beaufort,text) = intentconfig.get_beauforttext(float(speed))
            log.debug(f"after beaufort: {beaufort},{speed},{text}")
            speed = intentconfig.replace_decimal_point(speed)
            speech = intentconfig.get_text(intentconfig.DomoText.GetWind_Response)
            direction = intentconfig.get_text(intentconfig.DomoText.GetWind_Direction, direction)
            self.intentjson.set_speech(speech.format(SPEED=speed, DIRECTION=direction,
                BEAUFORT=beaufort, BEAUFORT_TEXT=text ))
        else:
            log.warning(f"Error returned for idx:{idx}."\
                + f"\n-----json--------\n{res_json}\n-----end json--------\n")
            speech = intentconfig.get_text(intentconfig.DomoText.Error)
            self.intentjson.set_speech(speech)

    def get_json_value(self, res_json, name, default=""):
        if name in res_json:
            return res_json[name]
        return default


    def doDomoSun(self):
        '''
            Return the data for dusk, sunrise, sunset and dawn.
            Data is retrieved from domoticz.
            Example JSON return:
                {
                  "ActTime": 1623943842,
                  "AstrTwilightEnd": "00:00",
                  "AstrTwilightStart": "00:00",
                  "CivTwilightEnd": "22:55",
                  "CivTwilightStart": "04:28",
                  "DayLength": "16:48",
                  "NautTwilightEnd": "00:16",
                  "NautTwilightStart": "03:06",
                  "ServerTime": "2021-06-17 17:30:42",
                  "SunAtSouth": "13:41",
                  "Sunrise": "05:17",
                  "Sunset": "22:05",
                  "app_version": "2020.2",
                  "status": "OK",
                  "title": "Devices"
                }
            The result is returned in tags DAWN, SUNRISE, SUNSET and DUSK
            in the speech slot
        '''
        # get slots
        speech = self.intentjson.get_slot_value("speech")
        if not speech:
            error_missing_parameter("speech","DomoSun")

        # perform action
        res_json = self.domo.get_info()
        log.debug(str(res_json))
        
        dawn = self.get_json_value(res_json,"CivTwilightStart").replace(':',' ')
        sunrise = self.get_json_value(res_json,"Sunrise").replace(':',' ')
        sunset = self.get_json_value(res_json,"Sunset").replace(':',' ')
        dusk = self.get_json_value(res_json,"CivTwilightEnd").replace(':',' ')

        # format speech result
        if "DAWN" in speech:
            speech = speech.replace('DAWN', dawn)
        if "SUNRISE" in speech:
            speech = speech.replace('SUNRISE', sunrise)
        if "SUNSET" in speech:
            speech = speech.replace('SUNSET', sunset)
        if "DUSK" in speech:
            speech = speech.replace('DUSK', dusk)

        self.intentjson.set_speech(speech)

    '''
    Get info from devices e.g.
    DomoGas   007 Type:P1 Smart Meter         SubType:Gas		   Data:5905.186      Name:Gas
            Counter:5905.186	CounterToday:3.380 m3,
    '''
    def doDomoGas(self):
        device = self.domo.get_device("P1 Smart Meter")
        if device :
            data = device["CounterToday"]
            data = re.sub(' .*','',data)
        else:
            data = ""


    '''
    DomoHumid 152 Type:Humidity				  SubType:LaCrosse TX3 Data:Humidity 50 % Name:dummy humidity
            Humidity:50	HumidityStatus:Comfortable,
    DomoHumid 019 Type:Temp + Humidity		  SubType:THGN122/123. Data:3.7 C 88 %    Name:Temp/Humid
            DewPoint:1.90	Humidity:88	HumidityStatus:Normal	Temp:3.7,
    DomoHumid 147 Type:Temp + Humidity + Baro SubType:THB1 - BTHR. Data:0.0 C 50 % 1010 hPa	Name:dummy temp hum baro
            Barometer:1010	DewPoint:-9.20	Forecast:1	ForecastStr:Sunny	Humidity:50	HumidityStatus:Comfortable	Temp:0.0,
    '''
    def doDomoHumid(self):
        device = self.domo.get_device("Humidity")
        if device :
            data = device["Humidity"]
        else:
            device = self.domo.get_device("Temp + Humidity")
            if device :
                data = device["Humidity"]
            else:
                device = self.domo.get_device("Temp + Humidity + Baro")
                if device :
                    data = device["Humidity"]
                else:
                    data = ""


    '''
    DomoBaro  147 Type:Temp + Humidity + Baro SubType:THB1 - BTHR..Data:0.0 C 50 %	1010 hPa	Name:dummy temp hum baro
            Barometer:1010	DewPoint:-9.20	Forecast:1	ForecastStr:Sunny	Humidity:50	HumidityStatus:Comfortable	Temp:0.0,
    DomoBaro  148 Type:Temp + Baro			  SubType:BMP085 I2C   Data:0.0 C 1038.0 hPa	Name:dummy temp baro
            Barometer:1038.0	Forecast:0	ForecastStr:Stable	Temp:0.0,
    '''
    def doDomoBaro(self):
        device = self.domo.get_device("Temp + Humidity + Baro")
        if device :
            data = device["Barometer"]
        else:
            device = self.domo.get_device("Temp + Baro")
            if device :
                data = device["Barometer"]
            else:
                data = ""


    '''
    DomoRain  143 Type:Rain					  SubType:TFA		   Data:0             Name:dummy rain
            Rain:0	RainRate:0,
    '''
    def doDomoRain(self):
        device = self.domo.get_device("Rain")
        if device :
            data = device["Data"]
            data = re.sub(' .*','',data)
        else:
            data = ""


    '''
    DomoTemp  019 Type:Temp + Humidity		  SubType:THGN122/123..Data:3.7 C 88 %    Name:Temp/Humid
            DewPoint:1.90	Humidity:88	HumidityStatus:Normal	Temp:3.7,
    DomoTemp  092 Type:Temp					  SubType:LaCrosse TX3 Data:66.2 C        Name:Internal Temperature
            Temp:66.2,
    DomoTemp  147 Type:Temp + Humidity + Baro SubType:THB1 - BTHR..Data:0.0 C 50 % 1010 hPa	Name:dummy temp hum baro
            Barometer:1010	DewPoint:-9.20	Forecast:1	ForecastStr:Sunny	Humidity:50	HumidityStatus:Comfortable	Temp:0.0,
    DomoTemp  148 Type:Temp + Baro			  SubType:BMP085 I2C   Data:0.0 C 1038.0 hPa Name:dummy temp baro
            Barometer:1038.0	Forecast:0	ForecastStr:Stable	Temp:0.0,
    DomoTemp  159 Type:Temp					  SubType:LaCrosse TX3 Data:0.0 C         Name:dummytemp
            Temp:0.0,
    '''
    def doDomoTemp(self):
        device = self.domo.get_device("Temp")
        if device :
            data = device["Temp"]
        else:
            device = self.domo.get_device("Temp + Humidity")
            if device :
                data = device["Temp"]
            else:
                device = self.domo.get_device("Temp + Humidity + Baro")
                if device :
                    data = device["Temp"]
                else:
                    data = ""


    '''
    DomoElec  006 Type:Usage				  SubType:Electric	   Data:345 Watt	  Name:Verbruik elektriciteit,
    DomoElec  156 Type:General				  SubType:kWh		   Data:0.000 kWh	  Name:dummy Electric (Instant+Counter)
            CounterToday:0.000 kWh	EnergyMeterMode:	Usage:0 Watt,
    '''
    def doDomoElec(self):
        device = self.domo.get_device("Usage","Electric")
        if device :
            data = device["Data"]
            data = re.sub(' .*','',data)
        else:
            device = self.domo.get_device("General","kWh")
            if device :
                data = device["CounterToday"]
                data = re.sub(' .*','',data) # remove everyting after first space
                data = re.sub('\.','',data)  # remove decimal point
                data = re.sub('^0*','',data) # remove leading zeroes
            else:
                data = ""


    '''
    DomoWind  020 Type:Wind					  SubType:WTGR800	   Data:112.5;ESE;0.0;0.0;3.7;0	Name:Wind
            Direction:112.5	DirectionStr:ESE	Gust:0.0	Speed:0.0,
    DomoWind  157 Type:Wind					  SubType:TFA		   Data:0;N;0;0;0;0	  Name:dummy Wind+Temp+Chill
            Chill:0.0	Direction:0.0	DirectionStr:N	Gust:0.0	Speed:0.0	Temp:0.0,
    DomoWind  158 Type:Wind					  SubType:WTGR800	   Data:0;N;0;0;0;0	  Name:dummy Wind
            Direction:0.0	DirectionStr:N	Gust:0.0	Speed:0.0,
    '''
    def doDomoWind(self):
        device = self.domo.get_device("Wind")
        if device :
            data = device["Data"]
            data = re.sub(' .*','',data)
        else:
            data = ""


    
    def doDomoUpdateSlots(self):
        question = intentconfig.get_text(intentconfig.DomoText.AskUpdateSlotsConfirmation)
        if self.rhasspy.rhasspy_confirm(question):
            self.rhasspy.rhasspy_speak(
                intentconfig.get_text(intentconfig.Text.Please_Wait))
            domo_rhasspy = Domo_Rhasspy(self.domo, self.rhasspy)
            confirmation = intentconfig.get_text(intentconfig.DomoText.SayUpdateSlotsConfirmation)
            self.intentjson.set_speech(confirmation)
            domo_rhasspy.create_slots_files()
        else:
            no_confirmation = intentconfig.get_text(intentconfig.DomoText.SayNoUpdateSlotsConfirmation)
            self.intentjson.set_speech(no_confirmation)

# End Of File