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

from rrdweather import RrdWeather
import json
import datetime

from watchdog import WatchdogThread
import subprocess
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
sample_interval = 10 

# ====================================================================
# End of configurable data
# ====================================================================


def mail_start():
    subject = "(Re)starting data gathering for weather station"
    body = f"(Re)starting receiving data for weather station on "\
           +f"{datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    print(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()

def mail_stop(elapsed_time):
    subject = "No data from weather station"
    body = f"No datareceived for {elapsed_time} seconds on "\
            + f"{datetime.datetime.now().strftime('%c')}"
    msg = f"To: {mail_to}\nFrom: {mail_from}\nSubject: {subject}\n{body}\n\n"
    print(f"Sending mail to {mail_to}\nMessage:\n{msg}")
    process = subprocess.Popen(["/usr/sbin/ssmtp", mail_to],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.communicate(msg.encode('utf-8'))
    process.stdin.close()


###### MAIN ############

if LOGDIR == '/home/pi/logexample/'\
  or rrdfiledir == "/home/pi/rrdexample/"\
  or mail_to == "mail@example.com"\
  or mail_from == "mail@example.com":
    print("Fix configuration first. Check configurable data in script")
    exit(1)
    
if __name__ == '__main__':

    formatstr = '%(asctime)s %(levelname)-4.4s %(module)-14.14s'\
                 +' (%(lineno)d)- %(message)s'
    logging.basicConfig(filename=LOGDIR+'rtl2rrd.log',
                        level=LOGLEVEL,
                        format=formatstr,
                        datefmt='%Y%m%d %H:%M:%S')

    log.info("starting rtl2rrd")

    wd = WatchdogThread.restart(mail_start,mail_stop,watchdog_period)
    rrdweather = RrdWeather(rrdfiledir)
    
    # Run: /usr/local/bin/rtl_433  -f 868288000 -F json
    proc = subprocess.Popen(
        ['/usr/local/bin/rtl_433', '-f','868288000' , '-F','json'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)

    line_in = ""
    while proc.poll() is None:
        line_in = proc.stdout.readline().rstrip()
        if line_in == "":
            errors = proc.stderr.readline().rstrip()
            log.info(f"stderr:{errors}")
            continue
        log.debug(f"Line:{line_in}")
        data_received = json.loads(line_in)
        res = rrdweather.update(data_received)
        if res is None:
            wd = WatchdogThread.restart(mail_start,mail_stop,
                                        watchdog_period,wd)
        else:
            log.info(f"Update returned with: [{res}]")

    log.warning(f"Exited with exitcode = {proc.returncode}")
    line_in = proc.stdout.readline().rstrip()
    while line_in:
        log.warning(f"stdout:{line_in}")
        line_in = proc.stdout.readline().rstrip()
    errors = proc.stderr.readline().rstrip()
    while errors != "":
        log.warning(f"stderr:{errors}")
        errors = proc.stderr.readline().rstrip()

# End of File