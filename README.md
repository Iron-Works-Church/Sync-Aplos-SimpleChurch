# Sync-Aplos-SimpleChurch
This is a simple program that synchronizes donations recorded in a SimpleChurch batch into Aplos accounting software.  This code was developed for Iron Works Church and will need to be modified to fit the specific use-case.  It is designed to run as an AWS Lambda function and uses SNS to email status and errors to those subscribed to the SNS topic.

Edit creds.json with your parameters to run.
