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
import fileinput
import json
import datetime
import sys
import os

from watchdog import WatchdogThread
import subprocess

from dsmr_parser import telegram_specifications
from dsmr_parser.clients import SerialReader, SERIAL_SETTINGS_V5
from dsmr_parser import obis_references
import requests
import logging

log = logging.getLogger(__name__)

# ====================================================================
# Begin of configurable data
# ====================================================================
# Path to the file with logging output
LOGDIR = '/home/pi/log/'

# LOGLEVEL can be set to logging.DEBUG, logging.INFO, logging.WARN,
#          logging.ERROR or logging.CRITICAL
LOGLEVEL = logging.DEBUG

# Directory to store rrd-files (MUST end with / if not empty!)
rrdfiledir="/home/pi/data2/"
# mail parameters for watchdog mails
mail_to = "albert.montijn@gmail.com"
mail_from = "a.montijn@chello.nl"
# send email when <watchdog_period> seconds passed since last update.
watchdog_period = 900
# number of samples to skip between database updates
sample_interval = 12 

# ====================================================================
# End of configurable data
# ====================================================================


def mail_start():
    subject = "(Re)starting data gathering from p1"
    body = f"(Re)starting receiving data from p1 at {datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    log.info(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()

def mail_stop(elapsed_time):
    subject = "No data from p1"
    body = f"No datareceived for {elapsed_time} seconds on {datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    log.info(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()

    # def update(self, input_data):
        # res = self.check_data(input_data)
        # if res is not None:
            # log.info(f"Check json returned {res}")
            # log.info(f"Input was [{str(input_data)}")
        # else:
            # data_datetime = self.get_datetime_for_update(input_data)
            # filename = rrd.get_file(data_datetime)
            # data = self.input_to_data(input_data)
            # res = rrdtool.updatev(filename,"-t",self.template,data)
            # if log.isEnabledFor(logging.DEBUG):
                # for key,value in res.items():
                    # log.debug(f"K:{key}={value}")
            # log.info(f'rrdtool.update({filename},{self.template},{data}')
        # return res
    # def jsoninput_to_data(self, json_data):
        # data_datetime = self.get_datetime_for_update(json_data)
        # timestamp = round(data_datetime.timestamp())
        # tempc = json_data["temperature_C"]
        # windm = json_data["wind_max_m_s"]
        # winda = json_data["wind_avg_m_s"]
        # windd = json_data["wind_dir_deg"]
        # humid = json_data["humidity"]
        # WARNING: COUNTER and DERIVE do NOT ACCEPT FLOATING POINT !?!?!
        # rainmm = str(int(10*json_data["rain_mm"]))
        # data = f"{timestamp}:{tempc}:{windm}:{winda}:{windd}:{humid}:{rainmm}"
        # return data
        
    def save_telegram(telegram):
        now = datetime.datetime.now()
        filename = rrd.checkfile(now)
        current_elec_watt = int(1000*telegram.CURRENT_ELECTRICITY_USAGE.value)
        hourly_gas_liter = int(1000*telegram.HOURLY_GAS_METER_READING.value)
        
        log.debug(f"Gas:{hourly_gas_liter}, Elec {current_elec_watt}")
            iso = datetime.datetime.fromtimestamp(int(data_items[0])).isoformat(sep=' ')
        
        time = 
        input_data = '{'
        updateData = str(round(now.timestamp()))+":"+str(current_elec_watt)+":"+str(hourly_gas_liter)
        res = rrdtool.updatev(filename,"-t",template,updateData)
        if log.isEnabledFor(logging.DEBUG):
            for k,v in res.items():
                log.debug("K:",k,"=",v)
            log.debug(f'rrdtool.update({filename},"-t",{template},{updateData})

if __name__ == '__main__':

    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s (%(lineno)d)'\
                 + '- %(message)s'
    logging.basicConfig(filename=LOGDIR+'p12rrd.log',
                        level=LOGLEVEL,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')

    log.info("starting p12rrd")

    wd = WatchdogThread.restart(mail_start,mail_stop,watchdog_period)

    rrdp1 = RrdP1(rrdfiledir)

    serial_reader = SerialReader(
        device='/dev/ttyUSB0',
        serial_settings=SERIAL_SETTINGS_V5,
        telegram_specification=telegram_specifications.V5
    )

    counter = 0
    for telegram in serial_reader.read_as_object():
        wd = WatchdogThread.restart(mail_start,mail_stop,watchdog_period,wd)
        if counter % sample_interval == 0:
            log.debug(f"Telegram {counter}:{str(telegram)}")
            save_telegram(telegram)

        counter += 1

# End of File