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
import boto3
from botocore.exceptions import ClientError

databaseURL = os.environ.get('DYNAMODBURL')

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

def dynamodbReadFromTable(databaseURL, tableName):
    print('dynamodbReadFromTable')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        configItems = []
        if tableName == 'cfg_nrvio_track':
            tableToRead = dynamodb.Table(tableName)
            x = tableToRead.scan()
            for i in x['Items']:
                # print(i['label'])
                configItems.append(i['label'])
        response = 'Configuration data successfully loaded.'
    except Exception as e:
        print('[ERROR] Failed to load configuration data from table ' + tableName + '.\n', e)
        response = 'Failed to load data'
        traceback.print_exc()
        pass
    return configItems

def dynamodbProvisionTable(databaseURL, tableName):
    print('dynamodbProvisionTable')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        if tableName == 'cfg_nrvio_track':
            tableToProvision = dynamodb.Table(tableName)
            tableToProvision.put_item(
            Item=json.loads('{"label":"Fullest disk"}')
            )
            tableToProvision.put_item(
            Item=json.loads('{"label":"High Disk Usage"}')
            )
            tableToProvision.put_item(
            Item=json.loads('{"label":"Layer 7 Disk Usage"}')
            )
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
        if tableName == 'cfg_nrvio_track':
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
        elif tableName == 'p7_interapp_msg':
            table = dynamodb.create_table(
                TableName=tableName,
                KeySchema=[
                    {
                        'AttributeName': 'action_name',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'action_status',
                        'KeyType': 'RANGE'  #Sort key
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'action_name',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'action_status',
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
    print('dynamodbTableCheck')
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

# Checking DB
# Table: cfg_nrvio_track
# Content: A list of New Relic violations to watch after
nrVioTrackList = []
if dynamodbTableCheck(databaseURL, 'cfg_nrvio_track') == 'Table not found':
    # Table missing - creating
    print('Table missing - creating')
    if dynamodbCreateTable(databaseURL, 'cfg_nrvio_track') == 'Table created':
        # Table created - provisioning
        print('Table created - provisioning')
        if dynamodbProvisionTable(databaseURL, 'cfg_nrvio_track') == 'Provisioning successful':
            nrVioTrackList = dynamodbReadFromTable(databaseURL, 'cfg_nrvio_track')
            print('Provisioning successful')
        else:
            print('Provisioning of table cfg_nrvio_track failed :-(')
    else:
        print('Creation of table cfg_nrvio_track failed :-(')
else:
    print('')
    nrVioTrackList = dynamodbReadFromTable(databaseURL, 'cfg_nrvio_track')

# if dynamodbDeleteTable(databaseURL, 'cfg_nrvio_track'):
#     print('')
# else:
#     print('Table cfg_nrvio_track deletion failed :-(')