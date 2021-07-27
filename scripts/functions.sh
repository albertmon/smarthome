#!/bin/bash

confirm(){
        echo -n "$1 (Y/n)" >>/dev/tty
        read ans
        case $ans in
        [nN]*) return 1;;
        esac
        return 0
}

# Based on script from https://unix.stackexchange.com/users/4358/phemmer
get_devices(){
        for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev)
        do
                syspath="${sysdevpath%/dev}"
                devname="$(udevadm info -q name -p $syspath)"
                # echo devname=$devname >&2
                [[ "$devname" == "bus/"* ]] && continue
                [[ "$devname" =~ "input/"* ]] && continue
                unset ID_SERIAL
                eval "$(udevadm info -q property --export -p $syspath)"
                [[ -z "$ID_SERIAL" ]] && continue
                # echo ID_SERIAL=$ID_SERIAL >&2
                echo "--device /dev/$devname "
        done
}

get_containername(){
	DEFAULT=$1
	CONTAINER_NAME=$DEFAULT
	confirm "Do you want to set the container name to $CONTAINER_NAME ? " ||
	while true
	do
		echo -n "Enter container name (only letters, digits or - or _ and starting with a letter)" >>/dev/tty
		read CONTAINER_NAME
		[[ -z "$CONTAINER_NAME" ]] && CONTAINER_NAME=$DEFAULT
		[[ ! "$CONTAINER_NAME" =~ ^[A-Za-z][-0-9A-Za-z_]*$ ]] && {
			echo "Illegal name!" >>/dev/tty
			continue
		}
		confirm "Do you want to set the container name to $CONTAINER_NAME ? " && break
	done
	echo $CONTAINER_NAME
}

#List of supported languages (used for profile)

LANGUAGES="ca-Catalan
cs-Czech
de-German
fr-French
el-Greek
en-English
es-Spanish
hi-Hindi
it-Italian
nl-Dutch
pl-Polish
pt-Portuguese
ru-Russian
sv-Swedish
vi-Vietnamese
zh-Chinese"

check_lang(){
	OK=""
	for LANGLINE in $LANGUAGES
	do
	  LANGCODE=$(echo $LANGLINE|sed 's/-.*//')
	  OK="$OK:$LANGCODE:"
	done
	echo $OK|grep -q $1
}

get_rhasspy_language(){
        DEFAULT=$1
        LANGUAGE=$DEFAULT
        confirm "Do you want to set the profile name to $LANGUAGE ? " ||
        while true
        do
		for LANG in $LANGUAGES
		do
			echo "	$LANG" |sed 's/-/ /' >>/dev/tty
		done
                echo -n "Enter language code: " >>/dev/tty
                read LANGUAGE
                [[ -z "$LANGUAGE" ]] && LANGUAGE=$DEFAULT
                check_lang $LANGUAGE || {
                        echo "Language $LANGUAGE not supported" >>/dev/tty
                        continue
                }
                confirm "Do you want to set the profile name to $LANGUAGE ? " && break
        done
        echo $LANGUAGE
}


