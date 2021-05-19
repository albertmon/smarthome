#!/bin/sh
SLEEPTIME=$1
DEVICE="plughw:CARD=USB,DEV=0"
SOUNDFILE=/profiles/nl/handler/${2:-alarm_clock_1.wav}
date >> /profiles/nl/handler/timer.log
echo "`date` Set timer Sleeptime=$SLEEPTIME, soundfile = $SOUNDFILE, pwd=`pwd`" >> /profiles/nl/handler/timer.log
(sleep $SLEEPTIME ; aplay -D $DEVICE $SOUNDFILE) >> /profiles/nl/handler/timer.log 2>&1 &

