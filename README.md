# terraform-lambda-trusted-advisor-sync
Sync AWS Trusted Advisor Cost Optimization recommendations to a DynamoDB table containing AWS cloud resources. The Terraform code provisions the necessary infrastructure to run the below AWS Lambda functions written in Python `3.7.x`.

*   *`AWS-Cost-Optimization-TrustedAdvisor-Sync`* - This Lambda function queries the AWS Trusted Advisor API and DynamoDB table to collect the relevant cost optimization recommendations and updates the DynamoDB table items.

## Running AWS Lambda Function

To run the AWS Lambda function in a different time, update the cron schedule for the following entries in the local `terraform.tfvars` file:

*   `ta_sync_event_schedule`

The Cron job schedule expression must be compliant with [AWS guidelines](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html).


