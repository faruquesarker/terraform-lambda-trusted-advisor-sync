import os
import logging
import json

import ec2

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

REGION=os.environ.get('REGION')
COST_REPORT_DDB_TABLE_NAME = os.environ.get("COST_REPORT_DDB_TABLE_NAME")
PARTITION_KEY = "EnvironmentName"
SORT_KEY = "Owner"
EC2_OPTIMIZE_ITEM_PREFIX = "OptimizeIdleEC2"
EC2_CHECK_METADATA_LEN = 22

def update_env_item(dynamodb_client, env_name, creator, service_type, check_metadata, opt_rec, ec2_id=None, lb_name=None):
    try:
        if service_type == 'EC2':
            attr_name = "%s.%s" %(EC2_OPTIMIZE_ITEM_PREFIX, ec2_id)
            LOG.info(f"Adding TA optimize: {attr_name}")
            if (len(check_metadata) != EC2_CHECK_METADATA_LEN) or (len(opt_rec) != EC2_CHECK_METADATA_LEN):
                LOG.warn(f"Mismatch in EC2 Check metadata len: {check_metadata} with optimization len: {opt_rec}")
            attr_val = {
                                        check_metadata[0]: {"S": str(opt_rec[0])},
                                        check_metadata[1]: {"S": str(opt_rec[1])},
                                        check_metadata[2]: {"S": str(opt_rec[2])},
                                        check_metadata[3]: {"S": str(opt_rec[3])},
                                        check_metadata[4]: {"S": str(opt_rec[4])},
                                        check_metadata[5]: {"S": str(opt_rec[5])},
                                        check_metadata[6]: {"S": str(opt_rec[6])},
                                        check_metadata[7]: {"S": str(opt_rec[7])},
                                        check_metadata[8]: {"S": str(opt_rec[8])},
                                        check_metadata[9]: {"S": str(opt_rec[9])},
                                        check_metadata[10]: {"S": str(opt_rec[10])},
                                        check_metadata[11]: {"S": str(opt_rec[11])},
                                        check_metadata[12]: {"S": str(opt_rec[12])},
                                        check_metadata[13]: {"S": str(opt_rec[13])},
                                        check_metadata[14]: {"S": str(opt_rec[14])},
                                        check_metadata[15]: {"S": str(opt_rec[15])},
                                        check_metadata[16]: {"S": str(opt_rec[16])},
                                        check_metadata[17]: {"S": str(opt_rec[17])},
                                        check_metadata[18]: {"S": str(opt_rec[18])},
                                        check_metadata[19]: {"S": str(opt_rec[19])},
                                        check_metadata[20]: {"S": str(opt_rec[20])},
                                        check_metadata[21]: {"S": str(opt_rec[21])},
                                     }
        
        response =  dynamodb_client.update_item(
                        TableName=COST_REPORT_DDB_TABLE_NAME,
                        Key={                        
                            "EnvironmentName": {"S": env_name },
                            "Owner": {"S": creator },
                        },
                        AttributeUpdates={
                              attr_name : {
                                    'Value': {
                                       'M': attr_val
                                    }
                                }
                        }
                    )
        return True
    except Exception as e:
        raise Exception(f"Error Updating App env:  {env_name}   recommendation info to DynamoDB Table {COST_REPORT_DDB_TABLE_NAME}: {e}")

def extract_tags(service_type, region, instance_id=None, lb_name=None):
    # Get resource tags
    creator = None
    env_name = None
    if service_type == 'EC2':
        tags = ec2.get_ec2_tags(instance_id)
    
    # Extract  creator and env name
    if tags and (service_type == 'EC2'):
        LOG.info("Got tags to be processed ===>: " + json.dumps(tags))
        for tag in tags:
            if 'Creator' in tag.get('Key'):
                creator = tag.get('Value')
            if 'Environment_name' in tag.get('Key'):
                env_name = tag.get('Value')
    return (env_name,creator)

def add_recommendation(dynamodb_client, check_metadata, check_result, service_type):
    # Get target resoucre IDs from the check result
    processed_time = check_result['timestamp']
    flagged_res = check_result['flaggedResources']
    LOG.info("Flagged resources: " + json.dumps(flagged_res))
    if flagged_res:
        flagged_res_count = len(check_result['flaggedResources'])
        print(f"Last TA check done at: {processed_time} w/ resource flagged: {flagged_res_count}")
        for res in flagged_res:
            opt_rec = res['metadata']            
            if (service_type == 'EC2'):
                ec2_id = res['metadata'][1]
                region = res['metadata'][0]
                (env_name, creator) = extract_tags(service_type, region, instance_id=ec2_id)
                LOG.info(f"Tag processed for {service_type} service: env --->: {env_name} creator: {creator}")   
                if env_name and creator:
                    LOG.info(f"Writing cost opt rec for {creator} env: {env_name}")
                    update_env_item(dynamodb_client, env_name, creator, service_type, check_metadata, opt_rec, ec2_id=ec2_id)
                    