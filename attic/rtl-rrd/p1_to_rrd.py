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
import datetime

from watchdog import WatchdogThread
import subprocess

from dsmr_parser import telegram_specifications
from dsmr_parser.clients import SerialReader, SERIAL_SETTINGS_V5
import logging

log = logging.getLogger(__name__)

# ====================================================================
# Begin of configurable data
# ====================================================================
# Path to the file with logging output
LOGDIR = '/home/pi/logexample/'

# LOGLEVEL can be set to logging.DEBUG, logging.INFO, logging.WARN,
#          logging.ERROR or logging.CRITICAL
LOGLEVEL = logging.DEBUG

# Directory to store rrd-files (MUST end with / if not empty!)
rrdfiledir="/home/pi/rrdexample/"
# mail parameters for watchdog mails
mail_to = "mail@example.com"
mail_from = "mail@example.com"
# send email when <watchdog_period> seconds passed since last update.
watchdog_period = 900
# number of samples to skip between database updates
sample_interval = 12 

# ====================================================================
# End of configurable data
# ====================================================================


def mail_start():
    subject = "(Re)starting data gathering from p1"
    body = f"(Re)starting receiving data from p1 at "\
           +f"{datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    log.info(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()

def mail_stop(elapsed_time):
    subject = "No data from p1"
    body = f"No datareceived for {elapsed_time} seconds on "\
           +f"{datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    log.info(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()

        
    def save_telegram(telegram):
        rrd.input_to_data(input_data)

###### MAIN ############

if LOGDIR == '/home/pi/logexample/'\
  or rrdfiledir == "/home/pi/rrdexample/"\
  or mail_to == "mail@example.com"\
  or mail_from == "mail@example.com":
    print("Fix configuration first. Check configurable data in script")
    exit(1)

if __name__ == '__main__':

    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s '\
                 +'(%(lineno)d)- %(message)s'
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
    while True:
        try:
            telegram = next(serial_reader.read_as_object())
        except UnicodeDecodeError:
            log.info("UnicodeDecodeError.")
            log.info(str(telegram))
            continue
    #for telegram in serial_reader.read_as_object():
        wd = WatchdogThread.restart(mail_start,mail_stop,watchdog_period,wd)
        if counter % sample_interval == 0:
            log.debug(f"Telegram {counter}:{str(telegram)}")
            data_received = rrdp1.input_to_data(telegram)
            res = rrdp1.update(data_received)

        counter += 1
