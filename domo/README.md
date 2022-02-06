# Domoticz
Tools and config files to transfer data to domoticz
## Transfer Weather data received using RTL_433 with SDR dongle
With these scripts you can automate the data reception and transfer

1.  First install rtl_433 

	Check the documentation for rtl_433  
	You can start with https://www.sensorsiot.org/install-rtl_433-for-a-sdr-rtl-dongle-on-a-raspberry-pi/  
2.	Copy the files to a directory (when needed)  

	There are 4 files (excluding this README.md):  
	
	|||
	|---|---|
	|**rtl_433.conf**|Configuration file for the rtl_433 program|  
	|**rtl_to_domoticz.py**|Python script that will run the rtl_433 program.|
	|**run_rtl_to_domoticz**|Shell script that will execute the Python code|
	|**smarthome.conf**|Configuration file with settings for|  
	||`rtl_config_file`: where is the rtl_433.conf file  |
	||`domoticz-url`: to which server and port must the data be sent  |
	||`domo_idx_temphum`: idx of domoticz device (type=Temp + Humidity)  |
	||`domo_idx_wind`: idx of domoticz device (type=Wind) |
	||`LOGFILE_PATH`, `LOGLEVEL`, `LOG_FORMAT`: logging parameters|
	||`POLL_INTERVAL`: minmal number of seconds between updates| 
	||`NO_DATA_TIMEOUT`: maximum number of seconds to wait (300 = 5 min)|
	||`GIVE_UP_TIMEOUT`: maximum number of seconds before quitting (3600 = 1 hour)|
	||`mail_to`, `mail_from`: mail addresses (uses /usr/sbin/ssmtp, must be installed)|
3.  Edit your crontab

	To start `run_rtl_to_domoticz` every time you reboot add the next line to your crontab (use `crontab -e`):
	
	> `@reboot sh /home/pi/domo/run_rtl_to_domoticz`

	Change the path to your location of `run_rtl_to_domoticz`

4.  Test your work!


For more info check the wiki: https://github.com/albertmon/smarthome/wiki
