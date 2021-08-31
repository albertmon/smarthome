#!/bin/bash

confirm(){
	echo -n "$1 (Y/n)" >> /dev/tty
	read ans
	case $ans in
	[nN]*) return 1;;
	esac
	return 0
}

get_restart(){
	confirm "Do you want to restart the container automatically ? " &&
		echo "--restart unless-stopped"
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
		[[ "$devname" =~ "snd/"* ]] && continue
		unset ID_SERIAL
		eval "$(udevadm info -q property --export -p $syspath)"
		[[ -z "$ID_SERIAL" ]] && continue
		# echo ID_SERIAL=$ID_SERIAL >&2
		echo "--device /dev/$devname "
	done
}

select_map(){
	echo "$1" >> /dev/tty; shift
	i=1
	while [[ $i -le $# ]]
	do
		eval echo "$i - \$$i." >> /dev/tty
		i=$(( $i + 1 ))
	done

	ans=-1
	until [[ -z "$ans" || "$ans" -ge 0 && "$ans" -le $# ]]
	do
		echo -n "Enter line number to change (0 or nothing to quit) " >> /dev/tty
		read ans
	done
	echo $ans
}

change_map(){
	num=$1
	new_value=$2
	map_org="$3"
	i=1
	for item in $map_org
	do
		if [[ $i -eq $num ]]
		then
			new=$(echo $item|awk -F: '{ print "'$new_value':" $2}')
		else
			new=$item
		fi
		new_map="$new_map $new"
		i=$(( $i + 1 ))
	done
	echo "$new_map"
}

edit_map(){
	prompt="$1"
	map="$2"
	num=$(select_map "$prompt" $map)
	while [[ ! -z "$num" && "$num" -ne 0 ]]
	do
		echo -n "Enter new value " >> /dev/tty
		read ans
		map=$(change_map $num $ans "$map")
		num=$(select_map "$prompt" $map)
	done
	echo "$map"
}

get_ports(){
	arg_ports="$1" # 123:456 789:0 ...
	prompt="Select line with port mapping to change"
	arg_ports=$(edit_map "$prompt" "$arg_ports")
	for p in $arg_ports
	do
		res="$res -p $p"
	done
	echo $res
}

get_volumes(){
	arg_volumes="$1"
	prompt="Select line with volume mapping to change"
	arg_volumes=$(edit_map "$prompt" "$arg_volumes")
	for v in $arg_volumes
	do
		res="$res -v $v"
	done
	echo $res
}

get_containername(){
	DEFAULT=$1
	CONTAINER_NAME=$DEFAULT
	confirm "Do you want to set the container name to $CONTAINER_NAME ? " ||
	while true
	do
		echo -n "Enter container name (only letters, digits or - or _ and starting with a letter)" >> /dev/tty
		read CONTAINER_NAME
		[[ -z "$CONTAINER_NAME" ]] && CONTAINER_NAME=$DEFAULT
		[[ ! "$CONTAINER_NAME" =~ ^[A-Za-z][-0-9A-Za-z_]*$ ]] && {
			echo "Illegal name!" >> /dev/tty
			continue
		}
		confirm "Do you want to set the container name to $CONTAINER_NAME ? " && break
	done
	echo "--name $CONTAINER_NAME"
}

