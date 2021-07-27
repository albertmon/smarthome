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
	confirm "Start domoticz with container-name $CONTAINER_NAME ? " ||
	while true
	do
		echo -n "Enter container name (only letters, digits or - or _ and starting with a letter)" >>/dev/tty
		read CONTAINER_NAME
		[[ -z "$CONTAINER_NAME" ]] && CONTAINER_NAME=$DEFAULT
		[[ ! "$CONTAINER_NAME" =~ ^[A-Za-z][-0-9A-Za-z_]*$ ]] && {
			echo "Illegal name!" >>/dev/tty
			continue
		}
		confirm "Start domoticz with container-name $CONTAINER_NAME ? " && break
	done
	echo $CONTAINER_NAME
}

