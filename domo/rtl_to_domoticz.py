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

import sys
import os
import signal
import subprocess

import threading
import logging
log = logging.getLogger(__name__)

# ====================================================================
# Get command-line parameters and read configuration data
# ====================================================================
import argparse
import configparser
#import traceback

def is_file_readable(filename):
    try:
        f = open(filename, "r")
        return True
    except FileNotFoundError:
        return False
    except PermissionError:
        return False


def get_args(default_config):
    default_config = os.path.expanduser(default_config)
    description = 'Receive data using RTL_433 dongle and send it to Domoticz'
    documentation = '''
        This program will listen indefinitely for messages received by a SDR_dongle
        The program starts rtl_433 for a predefined maximum number of seconds.
        When data is received and the time for an update of Domoticz has passed
        the data will be sent to Domoticz.
        The default configuration file is '''+default_config+'''
        Please goto https://github.com/albertmon/smarthome/wiki for more info
        '''
        
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description, 
        epilog=documentation)
    help_config = f"use config-file CONF. Default config-file = '{default_config}'"
    parser.add_argument('-t', '--test',help="test one time", action="store_true")
    parser.add_argument('-c', '--conf',help=help_config, type=argparse.FileType('r'),default=default_config)
    parser.add_argument("-v","--verbose", help="verbose output (NOT Logging!)", action="store_true")
    return parser.parse_args()

def get_config(config_file):
    config = {}
    config_parser = configparser.ConfigParser()
    config_parser.read_file(config_file)

    if "rtl_to_domoticz" in config_parser:
        my_options = config_parser["rtl_to_domoticz"]
    else:
        print(f"{configfile_name} has NO section(rtl_to_domoticz)")
        exit(1)

    try:
        # config file for rtl_433
        config["rtl_config_file"] =  os.path.expanduser(my_options.get('rtl_config_file',""))

        # Domoticz idx mappings
        config["domo_idx_temphum"] = my_options.getint('domo_idx_temphum',0)

        config["domo_idx_wind"] = my_options.getint('domo_idx_wind',0)

        config["formatstr"] = my_options.get("LOG_FORMAT",
            "%(asctime)s %(levelname)-4.4s %(module)-12.12s %(funcName)-10.10s (%(lineno)d)- %(message)s")
            
        # Path to the file with logging output
        config["LOGFILE_PATH"] = os.path.expanduser(my_options.get("LOGFILE_PATH","rtl_to_domoticz.log"))
        print(f"Logfile: {config['LOGFILE_PATH']}.")
        # LOGLEVEL can be set to logging.DEBUG, logging.INFO, logging.WARN,
        #          logging.ERROR or logging.CRITICAL
        config["LOGLEVEL"] = my_options.get("LOGLEVEL", "INFO")

        # URL to your Domoticz server
        config["DOMOTICZ_URL"] = my_options.get('DOMOTICZ_URL', "http://localhost:8080")

        # seconds to wait for next data gathering
        config["POLL_INTERVAL"] = my_options.getint('POLL_INTERVAL',30)  #  30

        # number of seconds before a timeout is reported and rtl_433 is restarted
        config["NO_DATA_TIMEOUT"] = my_options.getint('NO_DATA_TIMEOUT', 300)  # 300

        # number of seconds when to give up retrying
        config["GIVE_UP_TIMEOUT"] = my_options.getint('GIVE_UP_TIMEOUT',3600)  # 3600

        # mail parameters
        config["mail_to"] = my_options.get('mail_to', "")
        config["mail_from"] = my_options.get('mail_from', "")

    except ValueError as exc:
        print(f"Error in configfile ({configfile_name}): {exc}")
        sys.exit(1)

    except Exception as exc:
        print(f"Exception during configuring: {exc}")
#        print(f"{traceback.format_exc()}")
        sys.exit(1)

    return config


# ====================================================================
# End of configurable data
# ====================================================================

class WatchdogThread(threading.Thread):
    '''
    The class WatchdogThread implements a watchdog mechanism.
    After creating an instance of this class a thread is created that will
    run for <sleeptime> seconds. If the sleeptime is reached, the method 
    <action_stop> will be executed and the thread ends.
    if the method <restart> is called the running thread is ended and a new
    thread is started. This prevents the call of <action_stop>
    if <restart> is called when there is no thread running, <action_start> is
    called to inform the caller that the program resumed its normal course.
    Example:
    def action_start():
        print "program resumed"
    def action_stop():
        print "program stopped"
    watchdog_period = 10 # after 10 seconds the watchdog calls action_stop()
    
    # create and start the first watchdog thread
    wd = WatchdogThread.restart(action_start,action_stop,watchdog_period)

    while True:
        do_something_time_consuming_that_may_take_to_long()
        # restart the watchdog for a new <watchdog_period>
        wd = WatchdogThread.restart(action_start,action_stop,watchdog_period,wd)
        
    '''

    def __init__(self, action_start, action_stop, sleeptime=1800):
        # constructor, setting initial variables
        log.debug(f"New Watchdog with sleeptime={sleeptime}")
        self._stopevent = threading.Event(  )
        self._action_start = action_start
        self._action_stop = action_stop
        self._sleepperiod = 1
        self.sleep_time = sleeptime # default = 1800 = 30 minutes
        #WatchdogThread.thread_count += 1
        #name = f"watchdog_{WatchdogThread.thread_count}"

        threading.Thread.__init__(self) #, name=name)

    def run(self):
        """  main control loop """

        log.debug(f"Watchdog.run {threading.get_ident()}: sleeptime={self.sleep_time},nr of threads={threading.active_count()}")
        self._start_time = time.time()
        elapsed_time = 0
        while not self._stopevent.isSet(  ):
            elapsed_time += self._sleepperiod
            self._stopevent.wait(self._sleepperiod)
            if elapsed_time >= self.sleep_time:
                log.debug(f"Watchdog.run {threading.get_ident()}: Watchdog elapsed_time = {elapsed_time} >= {self.sleep_time} = self.sleep_time")
                self._action_stop(elapsed_time)
                return

    def join(self, timeout=None):
        # Stop the thread.
        seconds_run = time.time() - self._start_time
        log.debug(f"Watchdog.join ({seconds_run} seconds run) {threading.get_ident()}: with timeout={timeout},nr of threads={threading.active_count()}")
        self._stopevent.set(  )
        threading.Thread.join(self, timeout)

    def restart(action_start, action_stop, num_sec, old_thread=None):
        log.debug(f"in Watchdog.restart with old_thread={old_thread},nr of threads={threading.active_count()}")
        if old_thread is not None:
            if old_thread.is_alive():
                old_thread.join()
            else:
                old_thread._action_start()

        new_thread = WatchdogThread(action_start, action_stop, num_sec)
        new_thread.start()
        return new_thread

# end of class WatchdogThread


def send_mail(mail_to, msg):
    if mail_to :
        log.info(f"Sending mail to {mail_to}\nMessage:\n{msg}")
        process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        process.communicate(msg.encode('utf-8'))
        process.stdin.close()

def mail_program_ended(elapsed_time):
    if config["mail_to"] :
        subject = "No data from weather station"
        body = f"No datareceived for {elapsed_time} seconds on "\
                + f"{datetime.datetime.now().strftime('%c')}"\
                + f"\nProgram ended\n"

        msg = f"To: {config['mail_to']}\nFrom: {config['mail_from']}\nSubject: {subject}\n{body}\n\n"
        send_mail(config["mail_to"], msg)

def wd_start():
    log.info("(Re)starting data gathering for weather station")

def wd_stop(elapsed_time):
    log.info(f"watchdog stopped after {elapsed_time} seconds")
    log.debug(f"killing process: {proc.pid} with signal {signal.SIGKILL}.")
    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    mail_program_ended(elapsed_time)

def send_url(url):
    log.info(f"Url:[{url}]")

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

    get_url = f"{config['DOMOTICZ_URL']}/json.htm?type=command&param=udevice&idx={config['domo_idx_temphum']}&svalue={temp};{hum};{hum_stat}"
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

    get_url = f"{config['DOMOTICZ_URL']}/json.htm?type=command&param=udevice&idx={config['domo_idx_wind']}&svalue={wb};{wd};{ws};{wg};{temp};{temp_wc}"
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

    args = get_args("~/domo/smarthome.conf")
    verbose = args.verbose
    config = get_config(args.conf)

    logging.basicConfig(filename=config["LOGFILE_PATH"],
                        level=config["LOGLEVEL"],
                        format=config["formatstr"],
                        datefmt='%Y%m%d %H:%M:%S')

    log.info("starting rtl_to_domoticz")

    if config["rtl_config_file"] :
        if is_file_readable(config["rtl_config_file"]):
            cmd = ['/usr/bin/rtl_433','-c', config["rtl_config_file"]]
        else:
            print(f"File {config['rtl_config_file']} is not readable/existing")
            log.info(f"File {config['rtl_config_file']} is not readable/existing")
            exit(2)
    else :
        cmd = ['/usr/bin/rtl_433','-R','119','-f','868288000','-F','json']

    # Initialize last_time_sent to current time - POLL_INTERVAL
    # The first packet of data received will trigger a new last_time_sent
    last_time_sent = time.time() - config["POLL_INTERVAL"]

    wd = None
    while  time.time() < last_time_sent + config["GIVE_UP_TIMEOUT"] :
        # Wait until next Poll must be done:
        sleep_time = config["POLL_INTERVAL"] + last_time_sent - time.time()
        if sleep_time > 0 :
            log.debug(f"In loop: sleeping {sleep_time} seconds")
            time.sleep(sleep_time)

        # We will kill the rtl_433 process in wd_stop and restart it
        # in the while loop until the GIVE_UP_TIMEOUT is reached
        wd = WatchdogThread.restart(wd_start,wd_stop,config["NO_DATA_TIMEOUT"], wd)

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
                line_err = proc.stderr.readline().rstrip()
                while line_err != "":
                    if    not line_err.startswith("rtl_433 version unknown inputs ") \
                      and not line_err.startswith("Use -h for usage help")\
                      and not line_err.startswith("New defaults active"):
                        log.warning(f"stderr:{line_err}")
                    line_err = proc.stderr.readline().rstrip()
                continue  # skip error output

            # We received data on stdin
            log.debug(f"Line:{line_in}")
            data_received = json.loads(line_in)
            send_weather(data_received)
            log.debug(f"Weather info sent:{str(data_received)}")
            last_time_sent = time.time()

            wd = WatchdogThread.restart(wd_start,wd_stop,config["NO_DATA_TIMEOUT"],wd)

        # we arrive here when the rtl_433 process is stopped
        # and the poll function returned None
        # First we check the remaining output
        # rtl_433 is started in a new iteration 
        # (unless the GIVE_UP_TIMEOUT is reached
        line_err = proc.stderr.readline().rstrip()
        while line_err != "":
            if    not line_err.startswith("rtl_433 version unknown inputs ") \
              and not line_err.startswith("Use -h for usage help")\
              and not line_err.startswith("New defaults active"):
                log.warning(f"stderr:{line_err}")
            line_err = proc.stderr.readline().rstrip()
        if proc.returncode != 0 :
            log.warning(f"Subprocess: Exited with exitcode = {proc.returncode}. Waiting {config['NO_DATA_TIMEOUT']-config['POLL_INTERVAL']} seconds before retrying")
            time.sleep(config["NO_DATA_TIMEOUT"]-config["POLL_INTERVAL"])

        if args.test :
            last_time_sent = time.time()
            config["GIVE_UP_TIMEOUT"] = 0

    if wd :
        if wd.is_alive():
            if args.test :
                print(f"stop running thread ({wd})")
            wd.join()

    if args.test :
        print(f"Program ended, send mail")

    log.info(f"Program ended, send mail")
    mail_program_ended(int(time.time()-last_time_sent)) 

# End of File
