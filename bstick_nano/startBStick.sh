#!/bin/bash

echo 'Setting environment variables:'
echo -e '\t- BlinkStick instance identification'
export NAME='Barbon'
export NICKNAME='Barb'

echo -e '\t- Credentials'

echo -e '\t- Parameters...'
export DYNAMODBURL='http://ec2-3-25-212-0.ap-southeast-2.compute.amazonaws.com:8001'
export CB1DATAFOLDER='./bstick_data/'
export LOGSFOLDER='./log/'
export LOGFILENAME='bstick_default.log'
export CONFIGFILE='sample_config'
export P7INSTANCEID='p7##pantzumatic##mkultra##test'

echo -e '\t- Preferences...'
# 0 = OFF
# 1 = ON
export ENABLEBSTICK=1

echo 'Starting BlinkStick instance '$NAME' ($NICKNAME)'
python3 ./bstick.py

exit 0