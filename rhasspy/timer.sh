#!/bin/sh
# Script that sleeps for a number of seconds (First parameter)
# and plays a sound (optional second parameter)
# The wav-file must exist (when no second parameter is given:
# (/home/pi/.config/rhasspy)/profiles/nl/handler/alarm_clock.wav
# ############################################################################
# WARNING: Check the audio device!
# ############################################################################
# Configurable items:
# Audio device:
AUDIO_DEVICE="plughw:CARD=USB,DEV=0"

# Logfile:
# Path is absolute (root dir = /home/pi/.config/rhasspy)
LOGFILE=/profiles/nl/handler/timer.log
# Uncomment next line if no logging is desired
#LOGFILE=/dev/null

# End of configurable data

SLEEPTIME=$1
SOUNDFILE=${2:-/profiles/nl/handler/alarm_clock_1.wav}
date >> $LOGFILE
echo "`date` Set timer Sleeptime=$SLEEPTIME, soundfile = $SOUNDFILE, pwd=`pwd`" >> $LOGFILE
(sleep $SLEEPTIME ; aplay -D $AUDIO_DEVICE $SOUNDFILE) >> $LOGFILE 2>&1 &
