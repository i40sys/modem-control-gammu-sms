Detailed information at:
https://industry40.system/iot-gw/31
in spanish

quick summary of the operations:

# HOW DOES IT WORK

* only last SMS is maintained, the rest of SMS are deleted
* SMS content is stored in /var/run/modem, content always lowcase
* there are two scripts on /opt/modem: modem_on/modem_off
* both of them are linked on /usr/local/bin for making them available on PATH
* the only thing they do is change the content of /var/run/modem for on/off
* content of file /var/run/modem is overiden by last SMS content
* when modem is connected it's not possible to read SMS
* for disconnecting just run the command 'modem_off'
* in less than two minutes modem will be disconnected
* modem.py also works as a watchdog checking internet connection every 60"
* if desired state is 'on' the script run "wvdial internet"
* later checks if 'pppd' command is running, then a ping to Google DNS is sent
* if any of those two things fail 'wvdial internet' is running again
* when /var/run/modem content is 'off' process 'pppd' is killed

