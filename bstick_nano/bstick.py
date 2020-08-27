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
        elif tableName == 'p7dev_bstick':
            x = tableToRead.scan()
            print(x)
            for i in x['Items']:
                print(i['expiry'])
                retrievedItems.append(i['expiry'])
        response = 'Data successfully loaded.'
    except Exception as e:
        print('[ERROR] Failed to load configuration data from table ' + tableName + '.\n', e)
        response = 'Failed to load data.'
        traceback.print_exc()
        pass
    return retrievedItems

def dynamodbProvisionTable(databaseURL, tableName):
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
            tableToProvision.put_item(Item=json.loads('{"msgId":"20200827000000.000","expiry":"20200828000000","origin":"protocol7","tR":"255"}'))
            # tableToProvision.put_item(Item=json.loads('{"msgId":"20200827000000.000"}'))
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
# Table: p7dev_bstick
# Content: Commands destined to be used by the BlinkStick to set it's color (RGB) and mode (on, off, blinking)
msgList = []
tableName = 'p7dev_bstick'
if dynamodbTableCheck(databaseURL, tableName) == 'Table not found':
    # Table missing - creating
    print('Table missing - creating')
    if dynamodbCreateTable(databaseURL, tableName) == 'Table created':
        # Table created - provisioning
        print('Table created - provisioning')
        if dynamodbProvisionTable(databaseURL, tableName) == 'Provisioning successful':
            msgList = dynamodbReadFromTable(databaseURL, tableName)
            print('Provisioning successful')
        else:
            print(f'Provisioning of table {tableName} failed :-(')
    else:
        print(f'Creation of table {tableName} failed :-(')
else:
    print('')
    msgList = dynamodbReadFromTable(databaseURL, tableName)

if dynamodbDeleteTable(databaseURL, tableName):
    print('')
else:
    print(f'Table {tableName} deletion failed :-(')