#!/bin/env python
import json
import datetime
from datetime import date, time, datetime, timedelta
import requests
from aplos import *


# Import credentials

with open("creds.json", encoding='utf-8') as f:
    credentials = json.load(f)
    sc_user = credentials["sc_user"]
    sc_pass = credentials["sc_pass"]
    sc_baseurl = credentials["sc_baseurl"]
    s3_bucket = credentials["s3_bucket"]
    #aplos_api_id = credentials["aplos_api_id"]

# Define Funds



# Authenticate to SimpleChurch

def simplechurch_auth(sc_user, sc_pass, sc_baseurl):
    params = {"username": sc_user, "password": sc_pass}
    response = requests.get('{}user/login'.format(sc_baseurl), params=params)
    session_id = response.json()
    return(session_id["data"]["session_id"])

# Get batches for last 7 days

def get_batches(sc_session, sc_baseurl, relevant_batches):
    today = datetime.today()
    date_range = today - timedelta(days=7)
    params = {"session_id": sc_session}
    response = requests.get('{}giving/batches'.format(sc_baseurl), params=params)
    batches = response.json()
    for i in batches["data"]:
        batch_date = datetime.strptime(i["dateReceived"], "%Y-%m-%d")
        if batch_date > date_range:
            relevant_batches.append(i["id"])
    return(relevant_batches)

def get_batch_detail(sc_session, sc_baseurl, relevant_batches):
    funds = []
    batch_details = {}
    for i in relevant_batches:
        url = ''.join([sc_baseurl, "giving/batch/", str(i)])
        params = {"session_id": sc_session}
        response = requests.get(url, params=params)
        batches = response.json()
        batch_details["name"] = batches["data"]["name"]
        batch_details["date"] = batches["data"]["dateReceived"]
        batch_details["total"] = batches["expectedTotal"]
        if "Tithely" not in batches["data"]["name"]:
            if float(batches["data"]["expectedTotal"]) == batches["data"]["currentTotal"]:
                for i2 in batches["data"]["entries"]:
                    fund = i2["category"]["name"]
                    if fund not in batch_details:
                        batch_details[fund] = 0
                    batch_details[fund] = round((i2["amount"]), 2) + round(batch_details[fund], 2)
                check_aplos(batch_details)

def check_aplos(batch_details):
    params = {}
    params["f_rangestart"] = batch_details["date"]
    params["f_rangeend"] = batch_details["date"]
    aplos_transactions = api_transactions_get(api_base_url, api_id, api_access_token, params)
    for i in aplos_transactions["data"]["transactions"]:
        if i["note"] == batch_details["name"]:
            if i["amount"] == 


            
        


relevant_batches = []
sc_session = simplechurch_auth(sc_user, sc_pass, sc_baseurl)
get_batches(sc_session, sc_baseurl, relevant_batches)
get_batch_detail(sc_session, sc_baseurl, relevant_batches)
#aplostest()