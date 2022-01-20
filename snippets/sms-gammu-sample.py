#!/usr/bin/python3
from pprint import pprint
import gammu
# Gammu initialization
sm = gammu.StateMachine()
sm.ReadConfig()
sm.Init()


# SMS request
status = sm.GetSMSStatus()
count = status['SIMUsed'] + status['PhoneUsed'] + status['TemplatesUsed']
print(count)
if count == 0:
   exit

sms = sm.GetNextSMS(0,True)
#print(sms)
while True:
   #if sms[0]['State'] != 'Read':
   if True:
    print('-----------------------------------------------------------')
    #pprint(sms[0])
    print('DateTime: ', sms[0]['DateTime'])
    print('Number:   ', sms[0]['Number'])
    print('Location: ', sms[0]['Location'])
    print('State:    ', sms[0]['State'])
    print('Text:     ', sms[0]['Text'])
    print()
   count -= 1
   if count > 0:
     sms = sm.GetNextSMS(0,Location=sms[0]['Location'])
   else:
     break
