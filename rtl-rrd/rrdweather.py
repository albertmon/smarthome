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

import rrdtool
import json
import datetime

import os
import logging
from rrd import Rrd


class RrdWeather(Rrd):
    '''
    Rrd:
    def rrd_create_file(self):
        raise NotImplementedError
    def check_data(self, input_data):
        raise NotImplementedError
    def get_datetime_for_update(self, input_data):
        raise NotImplementedError
    def input_to_data(input_data):
        raise NotImplementedError
    def lastdata_to_json(data):
        raise NotImplementedError

    '''
    #{"time" : "2020-05-12 18:45:01",
    #"model" : "Bresser-5in1",
    #"id" : 233,
    #"temperature_C" : 10.400,
    #"humidity" : 60,
    #"wind_max_m_s" : 2.400,
    #"wind_avg_m_s" : 2.500,
    #"wind_dir_deg" : 247.500,
    #"rain_mm" : 61.200,
    #"mic" : "CHECKSUM"}

    # RRD parameters
    # Nr of seconds between updates
    stepsize  = 12
    # Number of updates to compute aggregation
    # So: 15 minutes results in 15*60/stepsize = 900/12 = 75 steps
    steps     = 75
    # maximum number of seconds that may pass between two updates of this data
    # source before the value of the data source is assumed to be *UNKNOWN*.
    # For our purpose (weather station) third of the steps can be omitted
    heartbeat = 300
    # for a rrd-file of 24 hours 24 * 4 = 96 rows will be sufficient
    rows      = 96
    # The xfiles factor defines what part of a consolidation interval may be made
    # up from *UNKNOWN* data while the consolidated value is still regarded as known.
    # It is given as the ratio of allowed *UNKNOWN* PDPs to the number of PDPs in
    # the interval. Thus, it ranges from 0 to 1 (exclusive).
    # Using an aggregation of 15 minutes we settle for a maximum loss of 80%
    xff       = 0.8
    model = "Bresser-5in1"
    template = "tempc:windm:winda:windd:humid:rainmm"

    def __init__(self, rrdfiledir):
        self.rrdfiledir = rrdfiledir
        Rrd.__init__(self)

    def rrd_create_file(self, my_datetime):
        filename = self.rrd_filename(my_datetime)
        starttimestamp = str(round(my_datetime.timestamp())-RrdWeather.stepsize)
        rrdtool.create(
           filename,
           "--start", starttimestamp,
           "--step", str(RrdWeather.stepsize),
        #DS:ds-name:{GAUGE|COUNTER|DERIVE|DCOUNTER|DDERIVE|ABSOLUTE}:heartbeat:min:max
           f"DS:tempc:GAUGE:{RrdWeather.heartbeat}:-40:50",
           f"DS:windm:GAUGE:{RrdWeather.heartbeat}:0:100",
           f"DS:winda:GAUGE:{RrdWeather.heartbeat}:0:100",
           f"DS:windd:GAUGE:{RrdWeather.heartbeat}:0:360",
           f"DS:humid:GAUGE:{RrdWeather.heartbeat}:0:100",
        # WARNING: COUNTER and DERIVE do NOT ACCEPT FLOATING POINT !?!?!
        # So we will store the value for rainmm times 10 and make it int
           f"DS:rainmm:DERIVE:{RrdWeather.heartbeat}:0:U",
        #RRA:{AVERAGE|MIN|MAX|LAST}:xfilefactor:steps:rows
           f"RRA:AVERAGE:{RrdWeather.xff}:{RrdWeather.steps}:{RrdWeather.rows}",
           f"RRA:MIN:{RrdWeather.xff}:{RrdWeather.steps}:{RrdWeather.rows}",
           f"RRA:MAX:{RrdWeather.xff}:{RrdWeather.steps}:{RrdWeather.rows}")
        log.info("Created file:"+filename)
        if log.isEnabledFor(logging.DEBUG):
            log.debug("==== rrd tool info ====")
            inf = rrdtool.info(filename)
            for key,value in inf.items():
                log.debug(f"K:{key}={value}")

    def get_datetime_for_update(self, input_data):
        return datetime.datetime.fromisoformat(input_data["time"])

    def input_to_data(self, input_data):
        data_datetime = datetime.datetime.fromisoformat(input_data["time"])
        timestamp = round(data_datetime.timestamp())
        tempc = input_data["temperature_C"]
        windm = input_data["wind_max_m_s"]
        winda = input_data["wind_avg_m_s"]
        windd = input_data["wind_dir_deg"]
        humid = input_data["humidity"]
        ## WARNING: COUNTER and DERIVE do NOT ACCEPT FLOATING POINT !?!?!
        rainmm = str(int(10*input_data["rain_mm"]))
        data = f"{timestamp}:{tempc}:{windm}:{winda}:{windd}:{humid}:{rainmm}"
        return data

    def get_wind_direction(self,wind_dir_deg):
        res = ["n","nne","ne","ene",\
                "e","ese","se","sse",\
                "s","ssw","sw","wsw",\
                "w","wnw","nw","nnw"]\
              [int((float(wind_dir_deg)+11.25)/22.5)]
        return res

    def lastdata_to_json(self,data):
        res = '{'
        if 'date' in data:
            res = res + f'"time":"'+ str(data['date']) + '"'
        if 'ds' in data:
            ds = data['ds']
            if 'tempc' in ds:
                res = res + f',"tempc":' + str(ds["tempc"])
            if 'windm' in ds:
                res = res + f',"windm":' + str(ds["windm"])
            if 'winda' in ds:
                res = res + f',"winda":' + str(ds["winda"])
            if 'windd' in ds:
                res = res + f',"windd":' + str(ds["windd"])
                res = res + f',"winddir":"' +\
                  str(self.get_wind_direction(ds["windd"])) + '"'
            if 'humid' in ds:
                res = res + f',"humid":' + str(ds["humid"])
            ## WARNING: COUNTER and DERIVE do NOT ACCEPT FLOATING POINT !?!?!
            # so rainmm is saved as str(int(10*input_data["rain_mm"]))
            if 'rainmm' in ds:
                res = res + f',"rainmm":' + str(int(ds["rainmm"])/10)
        res = res + '}'
        log.debug(f"Date:{data['date']}\nDS:{str(data['ds'])}")
        log.debug(f"get_lastdata:{res}")
        return(res)

    def check_input(self,input_data):
        return(input_data["model"] == self.model)

###### MAIN ############

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    else:
        arg = None

    LOGDIR = ""
    LOGLEVEL = logging.DEBUG
    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s (%(lineno)d)'\
                 + '- %(message)s'
    logging.basicConfig(filename=LOGDIR+'rrdweather.log',
                        level=LOGLEVEL,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')
    log = logging.getLogger("__name__")
    rrdweather = RrdWeather(rrdfiledir="/tmp/")

    if arg is None:
        date_ = datetime.datetime.now().isoformat(sep=' ')  # "2021-03-27 19:35:09"
        print(date_)
        jsoninput = '{"time" : "'+str(date_)+'", "model" : "Bresser-5in1",'\
                  + '"id" : 52, "battery_ok" : 1, "temperature_C" : 5.500, '\
                  + '"humidity" : 83, "wind_max_m_s" : 3.000, "wind_avg_m_s" :'\
                  + ' 2.100, "wind_dir_deg" : 247.500, "rain_mm" : 29.200,'\
                  + ' "mic" : "CHECKSUM"}'

        log.info(f"Before:{jsoninput}")
        input_data = json.loads(jsoninput)
        datastr = rrdweather.input_to_data(input_data)
        log.info(f"datastr={datastr}")
        rrdweather.update(jsoninput)
        #j2 = rrdweather.data_to_json(datastr)
        j2 = rrdweather.get_lastdata()
        log.info(f"After update:{j2}")

    elif arg == "lastupdate":
        data = rrdweather.get_lastdata()
        print(str(data))

