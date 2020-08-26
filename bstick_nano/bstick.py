#!/usr/bin/env python
import os
import time
import re
import urllib.request
import urllib.parse
import json
import traceback
from argparse import ArgumentParser
from colorama import Fore, Style, init
import redis, datetime, sys

endpoint = os.environ.get('REDISENDPOINT')

init(autoreset = True)

publicname = 'BlinkStick'
version = '0.1'

# Path to data folder (contains ML stuff)
cb1DataFolder = os.environ.get('CB1DATAFOLDER')
if not os.path.exists(cb1DataFolder):
    os.makedirs(cb1DataFolder)

def callURL(url2call, creds):
    try:
        print(Fore.LIGHTGREEN_EX + 'callURL')
        url = url2call
        req = urllib.request.Request(url, headers=creds)
        response = urllib.request.urlopen(req)
        payload = response.read()
        return payload
    except urllib.error.HTTPError:
        print(Fore.RED + '[HTTPError] Failed to call ' + str(url) + '\nProvider might be down or credentials might have expired.')
        return 'HTTPERROR'
        pass
    except urllib.error.URLError:
        print(Fore.RED + '[URLError] Failed to call ' + str(url) + '\nNetwork connection issue (check Internet access).')
        return "URLERROR"
        pass

def dynamodbTableCheck(databaseURL, tableName):
    try:
        print(Fore.LIGHTGREEN_EX + 'dynamodbTableCheck')
        dynamodb = boto3.client('dynamodb', endpoint_url=databaseURL)
        response = dynamodb.describe_table(TableName=tableName)
    # except dynamodb.exceptions.ResourceNotFoundException:
    except Exception as e:
        print('[DEBUG] DynamoDB table ' + tableName + ' not found')
        response = 'Table not found'
        # traceback.print_exc()
        pass
    return str(response)

def dynamodbListTableItems(databaseURL, tableName):
    try:
        print(Fore.LIGHTGREEN_EX + 'dynamodbListTableItems')
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToList = dynamodb.Table(tableName)
        tableToList.scan()
        response = tableToList.scan()
    except Exception as e:
        print('[ERROR] Failed to list content of database table ' + tableName + '.\n', e)
        response = 'Table listing failed'
        traceback.print_exc()
        pass
    return response

def writeDataToFile(targetFile, dataToWrite, successMsg, failureMsg, mode):
    print(Fore.LIGHTGREEN_EX + 'writeDataToFile')
    try:
        if mode == 'overwrite':
            newCB1File = open(targetFile,'w+')
        elif mode == 'append':
            newCB1File = open(targetFile,'a')
        newCB1File.write(dataToWrite)
        newCB1File.close()
        print(successMsg)
    except Exception as e:
        print(failureMsg, e)
        traceback.print_exc()
        pass

def prepareConn(endpoint):
	r = redis.StrictRedis(host=endpoint, port=6379, db=0, socket_timeout=1)
	return r

try:
    r = prepareConn(endpoint)
    r.mset({"Croatia": "Zagreb", "Bahamas": "Nassau"})
    r.get("Bahamas")
except Exception as e:
    print('[ERROR] An error occurred while talking to Redis: ', e)
    traceback.print_exc()
    pass