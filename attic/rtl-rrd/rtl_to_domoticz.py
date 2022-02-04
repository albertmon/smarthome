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

import json
import datetime
import time
import requests

from watchdog import WatchdogThread
import os
import signal
import subprocess

import threading
import logging
log = logging.getLogger(__name__)

# ====================================================================
# Begin of configurable data
# ====================================================================
# Domoticz idx mappings
domo_idx_temphum = 19
domo_idx_wind = 20

# Path to the file with logging output
LOGFILE_PATH = '/home/pi/log/rtl_to_domoticz.log'

# LOGLEVEL can be set to logging.DEBUG, logging.INFO, logging.WARN,
#          logging.ERROR or logging.CRITICAL
LOGLEVEL = logging.INFO

# URL to your Domoticz server
DOMOTICZ_URL = "http://domopi:8080"

# seconds to wait for next data gathering
POLL_INTERVAL = 30
# number of seconds before a timeout is reported and rtl_433 is restarted
NO_DATA_TIMEOUT = 300
# number of seconds when to give up retrying
GIVE_UP_TIMEOUT = 3600
 
mail_to = "test@example.com"
mail_from = "test@example.com"
rtl_config_file = '/home/pi/bin/rtl_433.conf'

# ====================================================================
# End of configurable data
# ====================================================================


def wd_start():
    log.info("(Re)starting data gathering for weather station")
    subject = "(Re)starting data gathering for weather station"
    body = f"(Re)starting receiving data for weather station on "\
           +f"{datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    log.info(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()

def wd_stop(elapsed_time):
    log.info(f"watchdog stopped after {elapsed_time} seconds")
    log.debug(f"killing process: {proc.pid} with signal {signal.SIGKILL}.")
    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    
def mail_program_ended(elapsed_time):
    subject = "No data from weather station"
    body = f"No datareceived for {elapsed_time} seconds on "\
            + f"{datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    log.info(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()


def send_url(url):
    log.debug(f"Sending Url:{url}.")

    try:
        res = requests.get(url)
        if res.status_code != 200:
            log.info(f"Result:{res.status_code}, text:{res.text}")
    except ConnectionError:
        log.error(f"ConnectionError for url {url} at {timestamp}")


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

    get_url = f"{DOMOTICZ_URL}/json.htm?type=command&param=udevice&idx={domo_idx_temphum}&svalue={temp};{hum};{hum_stat}"
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

    get_url = f"{DOMOTICZ_URL}/json.htm?type=command&param=udevice&idx={domo_idx_wind}&svalue={wb};{wd};{ws};{wg};{temp};{temp_wc}"
    send_url(get_url)

def send_weather(data):
    if data['model'] == 'Bresser-5in1':
        tempc = data["temperature_C"]
        windm = int(10 * float(data["wind_max_m_s"]))
        winda = int(10 * float(data["wind_avg_m_s"]))
        windd = data["wind_dir_deg"]
        humid = data["humidity"]
        rainmm = data["rain_mm"]
        send_wind(windd,winddir(windd),winda,windm,tempc)
        send_temp_hum(tempc,humid)

###### MAIN ############

if __name__ == '__main__':

    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-12.12s'\
                 +' %(funcName)-8.8s (%(lineno)d)- %(message)s'
    logging.basicConfig(filename=LOGFILE_PATH,
                        level=LOGLEVEL,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')

    log.info("starting rtl_to_domoticz")

    #cmd = ['/usr/bin/rtl_433','-R','119','-f','868288000','-F','json']
    cmd = ['/usr/bin/rtl_433','-c',rtl_config_file]
    # Initialize last_time_sent to current time - POLL_INTERVAL
    # The first packet of data received will trigger a new last_time_sent
    last_time_sent = time.time() - POLL_INTERVAL

    wd = None
    while  time.time() < last_time_sent + GIVE_UP_TIMEOUT :
        # Wait until next Poll must be done:
        sleep_time = POLL_INTERVAL + last_time_sent - time.time()
        if sleep_time > 0 :
            log.debug(f"In loop: sleeping {sleep_time} seconds")
            time.sleep(sleep_time)

        # We will kill the rtl_433 process in wd_stop and restart it
        # in the while loop until the GIVE_UP_TIMEOUT is reached
        wd = WatchdogThread.restart(wd_start,wd_stop,NO_DATA_TIMEOUT, wd)

        # The os.setsid() is passed in the argument preexec_fn so
        # it's run after the fork() and before exec() to run the shell.
        # We will kill and restart rtl_433 
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            universal_newlines=True)

        log.debug(f"started process {cmd}")

        # Read the output of rtl_433 process
        line_in = ""
        while proc.poll() is None:
            line_in = proc.stdout.readline().rstrip()
            if line_in == "":
                continue  # skip error output

            # We received data on stdin
            log.debug(f"Line:{line_in}")
            data_received = json.loads(line_in)
            send_weather(data_received)
            log.debug(f"Weather info sent:{str(data_received)}")
            last_time_sent = time.time()

            wd = WatchdogThread.restart(wd_start,wd_stop,NO_DATA_TIMEOUT,wd)

        # we arrive here when the rtl_433 process is stopped
        # and the poll function returned None
        # First we check the remaining output
        # rtl_433 is started in a new iteration 
        # (unless the GIVE_UP_TIMEOUT is reached
        if proc.returncode != 0 :
            log.warning(f"Subprocess: Exited with exitcode = {proc.returncode}")
        line_err = proc.stderr.readline().rstrip()
        while line_err != "":
            if not line_err.startswith("rtl_433 version unknown inputs ") \
              and not line_err.startswith("Use -h for usage help"):
                log.warning(f"stderr:{line_err}")
            line_err = proc.stderr.readline().rstrip()

    log.info(f"Program ended, send mail")
    mail_program_ended(int(time.time()-last_time_sent)) 

# End of File
