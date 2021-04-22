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

import subprocess
import logging
from rrd import Rrd


class RrdP1(Rrd):


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

    template = "current_elec_watt:hourly_gas_liter"

    def __init__(self, rrdfiledir):
        self.rrdfiledir = rrdfiledir
        Rrd.__init__(self)

    def rrd_create_file(self, my_datetime):
        filename = self.rrd_filename(my_datetime)
        starttimestamp = str(round(my_datetime.timestamp())-RrdP1.stepsize)
        rrdtool.create(
           filename,
           "--start", starttimestamp,
           "--step", str(RrdP1.stepsize),
#DS:ds-name:{GAUGE|COUNTER|DERIVE|DCOUNTER|DDERIVE|ABSOLUTE}:heartbeat:min:max
           f"DS:current_elec_watt:GAUGE:{RrdP1.heartbeat}:0:8000",
# WARNING: COUNTER and DERIVE do NOT ACCEPT FLOATING POINT !?!?!
           f"DS:hourly_gas_liter:DERIVE:{RrdP1.heartbeat}:0:U",
#RRA:{AVERAGE|MIN|MAX|LAST}:xfilefactor:steps:rows
           f"RRA:AVERAGE:{RrdP1.xff}:{RrdP1.steps}:{RrdP1.rows}",
           f"RRA:MIN:{RrdP1.xff}:{RrdP1.steps}:{RrdP1.rows}",
           f"RRA:MAX:{RrdP1.xff}:{RrdP1.steps}:{RrdP1.rows}")
        log.info("Created file:"+filename)
        if log.isEnabledFor(logging.DEBUG):
            log.debug("==== rrd tool info ====")
            inf = rrdtool.info(filename)
            for key,value in inf.items():
                log.debug(f"K:{key}={value}")

    def get_datetime_for_update(self, input_data):
        print("P1_MESSAGE_TIMESTAMP:"+str(input_data.P1_MESSAGE_TIMESTAMP.value))
        return input_data.P1_MESSAGE_TIMESTAMP.value

    def input_to_data(self, input_data):
        data_datetime = self.get_datetime_for_update(input_data)
        timestamp = round(data_datetime.timestamp())
        current_elec_watt = int(1000*input_data.CURRENT_ELECTRICITY_USAGE.value)
        hourly_gas_liter = int(1000*input_data.HOURLY_GAS_METER_READING.value)
        data = f"{timestamp}:{current_elec_watt}:{hourly_gas_liter}"
        return data

    def lastdata_to_json(self,data):
        res = '{'
        if 'date' in data:
            res = res + f'"time":"'+ str(data['date']) + '"'
        if 'ds' in data:
            ds = data['ds']
            if 'current_elec_watt' in ds:
                res = res + f',"current_elec_watt":'\
                 + str(ds["current_elec_watt"])
            if 'hourly_gas_liter' in ds:
                res = res + f',"hourly_gas_liter":'\
                 + str(ds["hourly_gas_liter"])
        res = res + '}'
        log.debug(f"Date:{data['date']}\nDS:{str(data['ds'])}")
        log.debug(f"get_lastdata:{res}")
        return(res)

    def check_input(self,input_data):
        return(True)

# End of File

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
    rrdp1 = RrdP1(rrdfiledir="/tmp/")

    if arg is None:
        from dsmr_parser import telegram_specifications
        from dsmr_parser.clients import SerialReader, SERIAL_SETTINGS_V5
        from dsmr_parser import obis_references
        from dsmr_parser.parsers import TelegramParser
        from dsmr_parser.objects import Telegram
        now = datetime.datetime.now()
        date_ = now.isoformat(sep=' ')  # "2021-03-27 19:35:09"
        print(date_)
        timestamp = now.strftime('%y%m%d%H%M%SW')
        print(timestamp)

        TELEGRAM_V5 = (
            '/ISk5\\2MT382-1000\r\n'
            '\r\n'
            '1-3:0.2.8(50)\r\n'
            '0-0:1.0.0('+ timestamp + ')\r\n'
            '0-0:96.1.1(4B384547303034303436333935353037)\r\n'
            '1-0:1.8.1(000004.426*kWh)\r\n'
            '1-0:1.8.2(000002.399*kWh)\r\n'
            '1-0:2.8.1(000002.444*kWh)\r\n'
            '1-0:2.8.2(000000.000*kWh)\r\n'
            '0-0:96.14.0(0002)\r\n'
            '1-0:1.7.0(00.244*kW)\r\n'
            '1-0:2.7.0(00.000*kW)\r\n'
            '0-0:96.7.21(00013)\r\n'
            '0-0:96.7.9(00000)\r\n'
            '1-0:99.97.0(0)(0-0:96.7.19)\r\n'
            '1-0:32.32.0(00000)\r\n'
            '1-0:52.32.0(00000)\r\n'
            '1-0:72.32.0(00000)\r\n'
            '1-0:32.36.0(00000)\r\n'
            '1-0:52.36.0(00000)\r\n'
            '1-0:72.36.0(00000)\r\n'
            '0-0:96.13.0()\r\n'
            '1-0:32.7.0(0230.0*V)\r\n'
            '1-0:52.7.0(0230.0*V)\r\n'
            '1-0:72.7.0(0229.0*V)\r\n'
            '1-0:31.7.0(0.48*A)\r\n'
            '1-0:51.7.0(0.44*A)\r\n'
            '1-0:71.7.0(0.86*A)\r\n'
            '1-0:21.7.0(00.070*kW)\r\n'
            '1-0:41.7.0(00.032*kW)\r\n'
            '1-0:61.7.0(00.142*kW)\r\n'
            '1-0:22.7.0(00.000*kW)\r\n'
            '1-0:42.7.0(00.000*kW)\r\n'
            '1-0:62.7.0(00.000*kW)\r\n'
            '0-1:24.1.0(003)\r\n'
            '0-1:96.1.0(3232323241424344313233343536373839)\r\n'
            '0-1:24.2.1(170102161005W)(00000.107*m3)\r\n'
            '0-2:24.1.0(003)\r\n'
            '0-2:96.1.0()\r\n'
            '!6EEE\r\n'
        )
        # 17-01-02-1920-02 W
        parser = TelegramParser(telegram_specifications.V5,apply_checksum_validation=False)
        telegram = parser.parse(TELEGRAM_V5)
        telegram = Telegram(TELEGRAM_V5, parser, telegram_specifications.V5)
        # message_datetime = telegram[obis_references.P1_MESSAGE_TIMESTAMP].value
        message_datetime = telegram.P1_MESSAGE_TIMESTAMP.value
        print(message_datetime)
        print(type(message_datetime))
        timestamp = message_datetime.timestamp()
        print(timestamp)

        datastr = rrdp1.input_to_data(telegram)
        log.info(f"datastr={datastr}")
        rrdp1.update(telegram)
        #j2 = rrdp1.data_to_json(datastr)
        j2 = rrdp1.get_lastdata()
        log.info(f"After update:{j2}")

    elif arg == "lastupdate":
        data = rrdp1.get_lastdata()
        print(str(data))

