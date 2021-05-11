#!/usr/bin/env python3
'''Copyright (c) 2020 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.'''


import requests
import json
import sys
import urllib3
import time
from collections import defaultdict
import csv
import smtplib


def addIdentifyingInfo(id, server, admin, pw, user_dict):
    search_url = '{}/vmrest/users?query=(alias is {})'.format(server, id)
    search = requests.get(search_url, auth=(admin, pw), verify=False,
        headers={'Accept': 'application/json'})

    if search.status_code == 200:
        search = search.json()

        if search['@total'] == '1':
            search_user = search['User']
            user_dict['obj_id'] = search_user['ObjectId']
            user_dict['first_name'] = search_user['FirstName']
            user_dict['last_name'] = search_user['LastName']

        else:
            print('No user with that id was found.')
            sys.exit(1)

    else:
        print('The status code of the search was not 200.')
        sys.exit(1)


def addCUPIInfo(server, admin, pw, user_dict):
    cupi_url = '{}/vmrest/users/{}'.format(server, user_dict['obj_id'])
    cupi_info = requests.get(cupi_url, auth=(admin, pw), verify=False,
        headers={'Accept': 'application/json'})

    if cupi_info.status_code == 200:
        cupi_info = cupi_info.json()
        user_dict['building'] = cupi_info['Building']
        user_dict['manager'] = cupi_info['Manager']
        user_dict['alias'] = cupi_info['Alias']
        user_dict['billing_id'] = cupi_info['BillingId']
        user_dict['creation_time'] = cupi_info['CreationTime']
        user_dict['department'] = cupi_info['Department']
        user_dict['display_name'] = cupi_info['DisplayName']
        user_dict['email_address'] = cupi_info['EmailAddress']
        user_dict['employee_id'] = cupi_info['EmployeeId']
        user_dict['ldap_type'] = cupi_info['LdapType']
        user_dict['ldap_user_id'] = cupi_info['LdapCcmUserId']
        user_dict['smtp_address'] = cupi_info['SmtpAddress']
        user_dict['title'] = cupi_info['Title']
        user_dict['extension'] = cupi_info['DtmfAccessId']

    else:
        print('The status code of the user info search was not 200.')
        sys.exit(1)

    login_info_url = '{}/vmrest/users/{}/credential/password'.format(server, user_dict['obj_id'])
    login_info = requests.get(login_info_url, auth=(admin, pw), verify=False,
        headers={'Accept': 'application/json'})

    if login_info.status_code == 200:
        login_info = login_info.json()
        user_dict['failed_login_count'] = login_info['HackCount']

    else:
        print("The status code of the messages API call was not 200.")
        sys.exit(1)


def addCUMIInfo(server, admin, pw, user_dict):
    read_url = '{}/vmrest/mailbox/folders/inbox/messages?userobjectid={}&read=true'.format(server, user_dict['obj_id'])
    read_info = requests.get(read_url, auth=(admin, pw), verify=False,
        headers={'Accept': 'application/json'})

    if read_info.status_code == 200:
        read_info = read_info.json()
        if 'Message' in read_info.keys():
            read_messages = read_info['Message']
            user_dict['total_read_30days'] = count30Day(read_messages)
        else:
            user_dict['total_read_30days'] = 'n/a'

    else:
        print('The status code of the messages API call was not 200.')
        sys.exit(1)

    unread_url = '{}/vmrest/mailbox/folders/inbox/messages?userobjectid={}&read=false'.format(server, user_dict['obj_id'])
    unread = requests.get(unread_url, auth=(admin, pw), verify=False,
        headers={'Accept': 'application/json'})

    if unread.status_code == 200:
        unread = unread.json()
        user_dict['total_unread'] = unread['@total']
        if 'Message' in unread.keys():
            unread_messages = unread['Message']
            user_dict['oldest'] = getOldestMessageInDays(unread_messages)
        else:
            user_dict['oldest'] = 'n/a'

    else:
        print('The status code of the unread voicemail search was not 200.')
        sys.exit(1)


#return the age of the oldest unread message in days
def getOldestMessageInDays(messages):
    oldest = messages[0]['ArrivalTime']

    for message in messages:
        if message['ArrivalTime'] < oldest:
            oldest = message['ArrivalTime']

    oldest_age_days = int((time.mktime(time.localtime()) - (int(oldest) / 1000)) / 86400)

    return oldest_age_days


def count30Day(messages):
    count_30day = 0

    for message in messages:
        if (time.mktime(time.localtime()) - (int(message['ArrivalTime']) / 1000)) / 86400 <= 30:
            count_30day += 1

    return count_30day
