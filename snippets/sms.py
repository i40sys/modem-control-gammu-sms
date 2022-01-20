#!/usr/bin/python3
from pprint import pprint
import logging
import gammu
import copy

DESIRED_DEFAULT = "on"
MODEM_FILE = "/var/run/modem"

# create logger
logger = logging.getLogger('modem')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

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
    logger.debug('getting last SMS received + ')
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

if __name__ == "__main__":
  get_last_sms()