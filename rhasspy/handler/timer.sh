#!/bin/bash

SLEEPTIME=$1
BASEDIR=${RHASSPY_PROFILE_DIR:-/profiles/nl}
SOUNDFILE=$BASEDIR/handler/${2:-alarm_clock_1.wav}
LOGFILE=$BASEDIR/handler/timer.log

echo "`date` Set timer Sleeptime=$SLEEPTIME, soundfile = $SOUNDFILE, pwd=`pwd`" >> $LOGFILE

eval set -- $(grep "command=rhasspy-speakers-cli-hermes" $BASEDIR/supervisord.conf)

while [ $# -gt 0 ] && [ "$PLAY_COMMAND" = "" ]
do 
	if [ "$1" = "--play-command" ]
	then
		PLAY_COMMAND="$2"
	fi
	shift
done

(sleep $SLEEPTIME ; $PLAY_COMMAND $SOUNDFILE) >> $LOGFILE 2>&1 &
