MAX_ITEMS = 100
PAGE_SIZE = 30
STARTING_TOKEN = None

from botocore.exceptions import ClientError

def refresh_ta_check(support_client, check_id):
    """
    TODO - Identify when to refresh the TA checks to fetch lastest findings
    """
    try:
        response = support_client.refresh_trusted_advisor_check(checkId=check_id)
        return response
    except ClientError as e:
        raise Exception(f"boto3 client error in describe_trusted_advisor_checks: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error in describe_trusted_advisor_checks: {e}")

def get_ta_cost_checks(support_client):
    try:
        response = support_client.describe_trusted_advisor_checks(language='en')
        checks = response["checks"]
        # Get the cost optimization checks
        cost_opt_checks = []
        for check in checks:
            for k,v in check.items():
                if  k == "category" and v == "cost_optimizing":
                    cost_opt_checks.append(check)
        return cost_opt_checks
    except ClientError as e:
        raise Exception(f"boto3 client error in describe_trusted_advisor_checks: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error in describe_trusted_advisor_checks: {e}")


def get_ta_check_result(support_client, check_id):
    try:
        response = support_client.describe_trusted_advisor_check_result(checkId=check_id, language='en')
        result = response["result"] if response else None
        if ('warning' in result['status']) or ('error' in result['status']): 
            return result
    except ClientError as e:
        raise Exception(f"boto3 client error in describe_trusted_advisor_checks: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error in describe_trusted_advisor_checks: {e}")

