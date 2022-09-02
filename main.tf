## Create necessary Infrastructure for deploying Lambda
# S3 bucket
resource "random_pet" "lambda_bucket_name" {
  prefix = "aws-cost-optimization"
  length = 4
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = random_pet.lambda_bucket_name.id

  acl           = "private"
  force_destroy = true

  tags = var.tags
}

# Retrieve DynamoDB table data
data "aws_dynamodb_table" "current" {
  name = var.dynamodb_table_name
}

# IAM policies and roles
resource "aws_iam_policy" "policy_ta_sync_lambda_exec_01" {
  name = "terraform-lambda-ta-sync-exec-01"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "support:DescribeTrustedAdvisorChecks",
          "support:DescribeTrustedAdvisorCheckResult",
          "support:RefreshTrustedAdvisorCheck",
          "cloudformation:ListStackResources",
          "cloudformation:DescribeStacks",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = ["dynamodb:BatchGetItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DescribeTable",
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
        ]
        Effect   = "Allow"
        # just a comment
        Resource = "${data.aws_dynamodb_table.current.arn}"
      },
      {
        "Sid" : "ListObjectsInBucket",
        "Effect" : "Allow",
        "Action" : ["s3:ListBucket"],
        "Resource" : "${aws_s3_bucket.lambda_bucket.arn}"
      },
      {
        "Sid" : "AllObjectActions",
        "Effect" : "Allow",
        "Action" : ["s3:*Object"],
        "Resource" : "${aws_s3_bucket.lambda_bucket.arn}/*"
      },
    ]
  })

  tags = var.tags
}

resource "aws_iam_role" "lambda_exec" {
  name = "aws_cost_optimization_ta_sync_lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      }
    ]
  })

  managed_policy_arns = [aws_iam_policy.policy_ta_sync_lambda_exec_01.arn, ]

  tags = var.tags
}


# Cost-Sync Lambda Fn and supporting inf
data "archive_file" "lambda_ta_sync" {
  type = "zip"

  source_dir  = "${path.module}/lambda/ta-sync"
  output_path = "${path.module}/lambda/ta-sync.zip"
}

resource "aws_s3_bucket_object" "lambda_ta_sync" {
  bucket = aws_s3_bucket.lambda_bucket.id

  key    = "ta-sync.zip"
  source = data.archive_file.lambda_ta_sync.output_path

  etag = filemd5(data.archive_file.lambda_ta_sync.output_path)

  tags = var.tags
}

resource "aws_lambda_function" "ta_sync" {
  function_name = "AWS-Cost-Optimization-TrustedAdvisor-Sync"

  s3_bucket = aws_s3_bucket.lambda_bucket.id
  s3_key    = aws_s3_bucket_object.lambda_ta_sync.key

  runtime = "python3.7"
  handler = "lambda_function.lambda_handler"

  source_code_hash = data.archive_file.lambda_ta_sync.output_base64sha256

  role = aws_iam_role.lambda_exec.arn

  timeout = 900 # set to max value

  environment {
    variables = {
      "COST_REPORT_DDB_TABLE_NAME" = data.aws_dynamodb_table.current.name,
      "REGION"                     = var.aws_region
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "ta_sync" {
  name = "/aws/lambda/${aws_lambda_function.ta_sync.function_name}"

  retention_in_days = 30

  tags = var.tags
}

#####  Scheduled Tasks #####
## Add Scheduled Tasks for Cost-Sync lambda functions
resource "aws_cloudwatch_event_rule" "ta_sync_event" {
  name                = "ta-sync-event"
  description         = "Cost Optimization Cost Sync Lambda - Fires at a given time"
  schedule_expression = var.ta_sync_event_schedule
}

resource "aws_cloudwatch_event_target" "run_ta_sync" {
  rule      = aws_cloudwatch_event_rule.ta_sync_event.name
  target_id = "ta_sync"
  arn       = aws_lambda_function.ta_sync.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_ta_sync" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ta_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ta_sync_event.arn
}
