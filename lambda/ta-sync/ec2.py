import boto3 
from botocore.exceptions import ClientError

ec2 = boto3.resource('ec2')

def get_ec2_tags(instance_id):
    try:
        ec2_instance =  ec2.Instance(instance_id)
        return getattr(ec2_instance, 'tags', None)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
            # Ignore the non-exist instances
            pass
        else:
             raise Exception(f"Unexpected error in EC2 get_tags: {e}")
    except Exception as e:
         raise Exception(f"Unexpected error in  in EC2 get_tags: {e}")
