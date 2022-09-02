import os
import logging
import json
from posix import environ
import boto3

import support
import dynamodb

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

TA_CHECK_NAME_EC2_LOW_UTILIZATION = 'Low Utilization Amazon EC2 Instances'

LOG.info('Loading Lambda function ta_sync...')

# Trusted Advisor 
support_client = boto3.client('support', region_name='us-east-1')

# DynamoDB
dynamodb_client = boto3.client('dynamodb')
COST_REPORT_DDB_TABLE_NAME = os.environ.get("COST_REPORT_DDB_TABLE_NAME")

def lambda_handler(event, context):
    ## Get TA Cost Optimization Checks
    cost_opt_checks = support.get_ta_cost_checks(support_client)
    LOG.info(("Found: " + str(len(cost_opt_checks)) + "Cost Optimization Checks."))
    LOG.debug("Cost Opt Checks: " + json.dumps(cost_opt_checks))

    for check in cost_opt_checks:
        for k,v in check.items():
            if k == 'name' and v == TA_CHECK_NAME_EC2_LOW_UTILIZATION:
                ec2_check_id = check['id']
                ec2_check_metadata = check['metadata']

    # Add recommendation for Idle EC2 instances
    ec2_check_result = support.get_ta_check_result(support_client, ec2_check_id)
    if ec2_check_result:
        LOG.info("EC2 Check result: " + json.dumps(ec2_check_result))
        dynamodb.add_recommendation(dynamodb_client, ec2_check_metadata, ec2_check_result, service_type='EC2')
      
    return {
        'statusCode': 200,
        'body': json.dumps('Success running Lambda RG Sync To Trusted Advisor!')
    }

