#!/bin/env python
import json
import datetime
from datetime import date, time, datetime, timedelta
import requests
from aplos import *
import boto3

# Define AWS SNS Client

sns = boto3.client('sns')
church_name = "Iron Works Church"

# Import credentials

with open("creds.json", encoding='utf-8') as f:
    credentials = json.load(f)
    sc_user = credentials["sc_user"]
    sc_pass = credentials["sc_pass"]
    sc_baseurl = credentials["sc_baseurl"]
    s3_bucket = credentials["s3_bucket"]
    api_id = credentials["aplos_api_id"]
    sns_topic = credentials["sns_topic"]

def lambda_handler(event, context):
    relevant_batches = []
    sc_session = simplechurch_auth(sc_user, sc_pass, sc_baseurl)
    get_batches(sc_session, sc_baseurl, relevant_batches)
    get_batch_detail(sc_session, sc_baseurl, relevant_batches)
    return {
        'statusCode': 200,
        'body': json.dumps('Completed')
    }

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
        batch_details["total"] = batches["data"]["expectedTotal"]
        batch_details["details"] = {}
        if "Tithely" not in batches["data"]["name"]:
            if float(batches["data"]["expectedTotal"]) == batches["data"]["currentTotal"]:
                for i2 in batches["data"]["entries"]:
                    fund = i2["category"]["name"]
                    #print(fund)
                    if fund not in batch_details["details"]:
                        batch_details["details"][fund] = {"id": 62, "amount": 0}
                    batch_details["details"][fund]["amount"] = round((i2["amount"]), 2) + round(batch_details["details"][fund]["amount"], 2)
                check_aplos(batch_details)

def check_aplos(batch_details):
    params = {}
    params["f_rangestart"] = batch_details["date"]
    params["f_rangeend"] = batch_details["date"]
    aplos_transactions = api_transactions_get(api_base_url, api_id, api_access_token, params)
    deposit_exists = False
    for i in aplos_transactions["data"]["transactions"]:
        if i["note"] == batch_details["name"] and "${:,.2f}".format(i["amount"]) == "${:,.2f}".format(float(batch_details["total"])):
            deposit_exists = True
    if deposit_exists:
        print("Deposit Exists - No action Taken")
    else:
        print("Making new Deposit")
        batch_details = match_funds(api_base_url, api_id, api_access_token, batch_details)
        add_deposit_aplos(api_base_url, api_id, api_access_token, batch_details)
    
def add_deposit_aplos(api_base_url, api_id, api_access_token, batch_details):
    headers = {'Authorization': 'Bearer: {}'.format(api_access_token)}
    print('Posting URL: {}transactions'.format(api_base_url))
    print('With headers: {}'.format(headers))
    line_num = 0
    payload = {
  "note": batch_details["name"],
  "date": batch_details["date"],
  "contact": {
     "companyname": church_name,
     "type": "company"
    },
    "lines": []
    }
    for k, v in batch_details["details"].items():
        payload["lines"].append({"amount": v["amount"], "account": {"account_number": 1000}, "fund": {"id": v["id"]}})
        payload["lines"].append({"amount": 0 - v["amount"], "account": {"account_number": 4000}, "fund": {"id": v["id"]}})
    jsonData = json.dumps(payload)
    r = requests.post(
        '{}transactions'.format(api_base_url), headers=headers, data=jsonData)
    api_error_handling(r.status_code)
    response = r.json()
    sns.publish(TopicArn=sns_topic, Message=('JSON response: {}'.format(response)))




def match_funds(api_base_url, api_id, api_access_token, batch_details):
    headers = {'Authorization': 'Bearer: {}'.format(api_access_token)}
    print('geting URL: {}funds'.format(api_base_url))
    print('With headers: {}'.format(headers))
    r = requests.get('{}funds'.format(api_base_url), headers=headers)
    api_error_handling(r.status_code) 
    response1 = {}
    response1 = r.json()
    for i, v in batch_details["details"].items():
        for i2 in response1["data"]["funds"]:
            if i == i2["name"]:
                v["id"] = i2["id"]
        if v["id"] is 62:
            sns.publish(TopicArn=sns_topic, Message="fund " + i + " does not match anything in aplos")
            quit()
    return(batch_details)
 

    
  


            
        


