#!/usr/bin/env python
import os
import time
import datetime
from datetime import date, timedelta
import re
import urllib.request
import urllib.parse
import json
import traceback
from argparse import ArgumentParser
from colorama import Fore, Style, init
import boto3
from botocore.exceptions import ClientError

try:
    from blinkstick import blinkstick
except ImportError:
    print('Cannot import blinkstick. Run: pip3 install blinkstick')
    pass

init(autoreset = True)

publicname = os.environ.get('NAME')
nickname = os.environ.get('NICKNAME')
databaseURL = os.environ.get('DYNAMODBURL')
p7server = os.environ.get('P7INSTANCEID')
enableLocalBStick = os.environ.get('ENABLEBSTICK')
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

def dynamodbDeleteTable(databaseURL, tableName):
    print('dynamodbDeleteTable')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToDelete = dynamodb.Table(tableName)
        tableToDelete.delete()
        response = 'Deletion successful'
    except Exception as e:
        print('[ERROR] Failed to delete database table ' + tableName + '.\n', e)
        response = 'Table deletion failed'
        traceback.print_exc()
        pass
    return response

def dynamodbListTableItems(databaseURL, tableName):
    print('dynamodbListTableItems')
    try:
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

def dynamodbReadFromTable(databaseURL, tableName, p7server):
    print(f'dynamodbReadFromTable - databaseURL: {databaseURL} - tableName: {tableName}')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToRead = dynamodb.Table(tableName)
        retrievedItems = []
        if tableName == 'email_tracking':
            x = tableToRead.scan()
            for i in x['Items']:
                print(i['label'])
                retrievedItems.append(i['label'])
            return retrievedItems
        elif tableName == 'p7dev_bstick':
            x = tableToRead.scan()
            print(x)
            for i in x['Items']:
                if i['origin'] == p7server:
                    print(i['origin'])
                    tR = i['tR']
                    tG = i['tG']
                    tB = i['tB']
                    bR = i['bR']
                    bG = i['bG']
                    bB = i['bB']
                    topMode = i['topMode']
                    bottomMode = i['bottomMode']
            return tR, tG, tB, bR, bG, bB, topMode, bottomMode
        response = 'Data successfully loaded.'
    except Exception as e:
        print('[ERROR] Failed to load configuration data from table ' + tableName + '.\n', e)
        response = 'Failed to load data.'
        traceback.print_exc()
        pass

def dynamodbProvisionTable(databaseURL, tableName, dataToInsert):
    print('dynamodbProvisionTable')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToProvision = dynamodb.Table(tableName)
        if tableName == 'email_tracking':
            tableToProvision.put_item(
            Item=json.loads('{"label":"Fullest disk"}')
            )
            tableToProvision.put_item(
            Item=json.loads('{"label":"High Disk Usage"}')
            )
            tableToProvision.put_item(
            Item=json.loads('{"label":"Layer 7 Disk Usage"}')
            )
        elif tableName == 'p7dev_bstick':
            print('Provision p7dev_bstick')
            tableToProvision.put_item(Item=json.loads(dataToInsert))
        response = 'Provisioning successful'
    except Exception as e:
        print('[ERROR] Failed to create database table ' + tableName + '.\n', e)
        response = 'Table provisioning failed'
        traceback.print_exc()
        pass
    return response

def dynamodbCreateTable(databaseURL, tableName):
    print('dynamodbCreateTable')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        if tableName == 'email_tracking':
            table = dynamodb.create_table(
                TableName=tableName,
                KeySchema=[
                    {
                        'AttributeName': 'label',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'label',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=tableName)
            print(table.item_count)
            response = 'Table created'
        elif tableName == 'p7dev_bstick':
            table = dynamodb.create_table(
                TableName=tableName,
                KeySchema=[
                    {
                        'AttributeName': 'msgId',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'msgId',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=tableName)
            print(table.item_count)
            response = 'Table created'
    except Exception as e:
        print('[ERROR] Failed to create database table ' + tableName + '.\n', e)
        response = 'Table creation failed'
        traceback.print_exc()
        pass
    return response

def dynamodbTableCheck(databaseURL, tableName):
    print(f'dynamodbTableCheck - databaseURL: {databaseURL}, tableName: {tableName}')
    try:
        dynamodb = boto3.client('dynamodb', endpoint_url=databaseURL)
        response = dynamodb.describe_table(TableName=tableName)
    except Exception as e:
        print(f'[DEBUG] DynamoDB table {tableName} not found', e)
        response = 'Table not found'
        pass
    return str(response)

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

def update_local_bstick_nano(tR, tG, tB, bR, bG, bB, topMode, bottomMode, enableLocalBStick):
    # This function drives the local BlinkStick Nano (two LEDs, one on each side)
    if enableLocalBStick == '1':
        try:
            if topMode == 'on':
                for bstick in blinkstick.find_all():
                    bstick.set_color(channel=0, index=0, red=int(tR), green=int(tG), blue=int(tB))
                time.sleep(0.1)
                bstickStatus = topMode
            elif topMode == 'flash':
                for bstick in blinkstick.find_all():
                    bstick.blink(channel=0, index=0, red=int(tR), green=int(tG), blue=int(tB), repeats=1, delay=500)
                time.sleep(0.1)
                bstickStatus = topMode
            elif topMode == 'off':
                for bstick in blinkstick.find_all():
                    bstick.set_color(channel=0, index=0, red=0, green=0, blue=0)
            if bottomMode == 'on':
                for bstick in blinkstick.find_all():
                    bstick.set_color(channel=0, index=1, red=int(bR), green=int(bG), blue=int(bB))
                time.sleep(0.1)
                bstickStatus = topMode
            elif bottomMode == 'flash':
                for bstick in blinkstick.find_all():
                    bstick.blink(channel=0, index=1, red=int(bR), green=int(bG), blue=int(bB), repeats=1, delay=500)
                time.sleep(0.1)
                bstickStatus = topMode
            elif bottomMode == 'off':
                bstick.set_color(channel=0, index=1, red=0, green=0, blue=0)
        except Exception as e:
            print('[ERROR] Failed to update local Blinkstick color.\n', e)
            bstickStatus = 'unknown'
            traceback.print_exc()
            pass
    else:
        bstickStatus = 'disabled'
        for bstick in blinkstick.find_all():
            bstick.turn_off()
    return bstickStatus

bstickStatus = 'empty'
bstickParams = []
shortWait = 2

# Checking DB
# Table: p7dev_bstick
# Content: Commands destined to be used by the BlinkStick to set it's color (RGB) and mode (on, off, blinking)
print('Checking Protocol/7 server connection...')
tableName = 'p7dev_bstick'
if dynamodbTableCheck(databaseURL, tableName) == 'Table not found':
    # Table missing - creating
    print('Table missing - creating')
    if dynamodbCreateTable(databaseURL, tableName) == 'Table created':
        print(f'Creation of table {tableName} succeeded.')
        print('...success.')
    else:
        print(f'Creation of table {tableName} failed :-(')
        print('...failure.')
else:
    print('...success.')
    

print(Fore.RED + '################')
print(Fore.RED + '#  BlinkStick  #')
print(Fore.RED + '################')
print(Fore.GREEN + '')

while True:
    tR, tG, tB, bR, bG, bB, topMode, bottomMode = dynamodbReadFromTable(databaseURL, tableName, p7server)
    print(f'tR: {tR}, tG: {tG}, tB: {tB}, bR: {bR}, bG: {bG}, bB: {bB}, topMode: {topMode}, bottomMode: {bottomMode}')
    update_local_bstick_nano(tR, tG, tB, bR, bG, bB, topMode, bottomMode, enableLocalBStick)
    time.sleep(shortWait)