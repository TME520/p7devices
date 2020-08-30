#!/bin/bash

echo 'Setting environment variables:'
echo -e '\t- BlinkStick instance identification'
export NAME='Merton'
export NICKNAME='Merton'

echo -e '\t- Credentials'

echo -e '\t- Parameters...'
export DYNAMODBURL='http://ec2-3-25-191-174.ap-southeast-2.compute.amazonaws.com:8001'
export CB1DATAFOLDER='./bstick_data/'
export LOGSFOLDER='./log/'
export LOGFILENAME='bstick_default.log'
export CONFIGFILE='sample_config'
export P7INSTANCEID='p7##pantzumatic##mugumugu##dev'

echo -e '\t- Preferences...'
# 0 = OFF
# 1 = ON
export ENABLEBSTICK=1

echo 'Starting BlinkStick instance '$NAME' ($NICKNAME)'
python3 ./bstick.py

exit 0
