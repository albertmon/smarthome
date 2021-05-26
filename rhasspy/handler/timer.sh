#!/bin/bash

SLEEPTIME=$1
BASEDIR=${RHASSPY_PROFILE_DIR:-/profiles/nl}
SOUNDFILE=$BASEDIR/handler/${2:-alarm_clock_1.wav}
LOGFILE=$BASEDIR/handler/timer.log

echo "`date` Set timer Sleeptime=$SLEEPTIME, soundfile = $SOUNDFILE, pwd=`pwd`" >> $LOGFILE

DEVICE=`python3 <<EOF
import json
f = open("$BASEDIR/profile.json", "r")
config = json.load(f)
device = config["sounds"]["aplay"]["device"]
print(device)
EOF
`

PLAY_COMMAND="aplay -q -t wav -D $DEVICE"

(sleep $SLEEPTIME ; $PLAY_COMMAND $SOUNDFILE) >> $LOGFILE 2>&1 &
