#!/usr/bin/env python3
import subprocess
import psutil
from ping3 import ping
import gammu
import copy
from time import sleep
import logging
import os

MODEM_DEVICE = "/dev/modem0"
#MODEM_DEVICE = "/dev/ttyUSB0"
MODEM_REAL_DEVICE = os.path.realpath(MODEM_DEVICE).split('/')[-1] # get real device, not the link
DESIRED_DEFAULT = "on"
MODEM_FILE = "/var/run/modem"
PING_IP = "8.8.8.8"

logger = logging.getLogger('modem')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def run_bg(cmd):
    logger.debug(' > run bg process:' + cmd)
    cp = subprocess.Popen( cmd, 
        shell = True,
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)
    #    universal_newlines=True, 

    #    close_fds=True) 
    #stdout, stderr = cp.communicate()
    #logger.debug(stdout)
    #logger.error(stderr)
    return cp

def run_wvdial(): 
    logger.debug('removing modem locks')
    cmd = "/usr/bin/lsof "+MODEM_REAL_DEVICE+" | /usr/bin/awk '{print $2}' | /usr/bin/tail -n +2 | /usr/bin/xargs kill -9"
    run_bg(cmd)
    cmd = "/usr/bin/rm /var/lock/LCK.." + MODEM_REAL_DEVICE
    run_bg(cmd)
    cmd = "/bin/fuser -k " + MODEM_REAL_DEVICE

    logger.debug('running wvdial')
    cmd = "/usr/bin/screen -d -m /usr/bin/wvdial -C /etc/wvdial.conf internet"
    run_bg(cmd)

    logger.debug('running wvdial: DONE')

    return True;

def pppd_is_running():
    logger.debug('checking pppd is alive')
    process_name = "pppd"

    for proc in psutil.process_iter():
        if proc.name() == process_name:
            logger.info('pppd alive')
            return True
    logger.info('pppd down')
    return False

def pppd_kill():
    logger.debug('killing pppd')
    process_name = "pppd"

    for proc in psutil.process_iter():
        if proc.name() == process_name:
            out = proc.kill()
            logger.info('pppd killed')
            return out
    logger.info('pppd not running')
    return False

def is_online():
    logger.debug('pinging google DNS')
    try:
        out = ping( PING_IP, timeout=10)
    except OSError:
        out = False
    if out:
        logger.info('online')
    else:
        logger.info('offline')
    return out

def _get_n_clean_sms():
  sm = gammu.StateMachine()
  sm.ReadConfig(Filename='/opt/modem/gammurc')
  sm.Init()

  status = sm.GetSMSStatus()

  count = status['SIMUsed'] + status['PhoneUsed'] + status['TemplatesUsed']
  sms = sm.GetNextSMS(0,True)
  last = {}
  current = {}
  while True:
    current['ts'] = sms[0]['DateTime']
    current['folder'] = sms[0]['Folder']
    current['location'] = sms[0]['Location']
    current['content'] = sms[0]['Text']
    logger.debug(f"[{current['folder']}/{current['location']}] \
      TS: {current['ts']} \
      C: {current['content']}")
    if 'ts' in last:
      logger.debug(f"current: {current['ts']} > last: {last['ts']}")
      if current['ts'] > last['ts']:
        logger.debug(f"deleting; folder: {last['folder']} - location: {last['location']}")
        sm.DeleteSMS(last['folder'], last['location'])
        last = copy.deepcopy(current)
    else:
      last = copy.deepcopy(current)

    count -= 1
    if count > 0:
      sms = sm.GetNextSMS(0,Location=sms[0]['Location'])
    else:
      break

  logger.info(f"Keeping: [{current['folder']}/{current['location']}] \
    TS: {current['ts']} \
    C: {current['content']}")
  return last['content'].rstrip()

def get_last_sms():
    logger.debug('getting last SMS received...')
    logger.debug('removing old SMS, keep the lastest one')
    last_sms_data = _get_n_clean_sms()
    # possible values: on/off -> online/offline
    if last_sms_data.lower() == "on":
        # echo on > /var/run/modem
        modem_desired_state = 'on'
    else:
        # echo off > /var/run/modem
        modem_desired_state = 'off'
    open(MODEM_FILE,'w').write(modem_desired_state)
    logger.debug(f"stored desired state {modem_desired_state} at {MODEM_FILE}")

def get_desired_state():
    try:
        out = open(MODEM_FILE,'r').read()
    except FileNotFoundError:
        out = DESIRED_DEFAULT
    return out.lower()

if __name__ == "__main__":
    # crontab calls periodically this business logic
    get_last_sms()
    if get_desired_state() == "on":
        logger.debug('Desired Internet connection: ONLINE')
        if not pppd_is_running():
            run_wvdial()
        else:
            if not is_online():
                logger.info("pppd running, Internet offline.")
                pppd_kill()
    else:
        logger.debug('Desired Internet connection: OFFLINE')
        if pppd_is_running():
            pppd_kill()
        else:
            get_last_sms()

    logger.debug('sleeping')

