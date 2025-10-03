variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "lambda_name" {
  description = "Lambda function name"
  type        = string
  default     = "vpc-api"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "vpcs"
}
