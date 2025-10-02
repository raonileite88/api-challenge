provider "aws" {
  region = var.region
}

# --- DynamoDB Table ---
resource "aws_dynamodb_table" "vpc_table" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "vpc_id"

  attribute {
    name = "vpc_id"
    type = "S"
  }
}

# --- IAM Role for Lambda ---
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "lambda_exec_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Attach policies
resource "aws_iam_role_policy_attachment" "lambda_ec2_dynamo" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_dynamo" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda Function ---
resource "aws_lambda_function" "vpc_api" {
  function_name = var.lambda_name
  runtime       = "python3.11"
  handler       = "app.lambda_handler"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "lambda.zip"

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.vpc_table.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_ec2_dynamo,
    aws_iam_role_policy_attachment.lambda_dynamo,
    aws_iam_role_policy_attachment.lambda_basic
  ]
}

# --- API Gateway ---
resource "aws_apigatewayv2_api" "vpc_api" {
  name          = "vpc-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.vpc_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.vpc_api.invoke_arn
}

# --- Cognito User Pool and Client ---
resource "aws_cognito_user_pool" "users" {
  name = "vpc-api-users"
}

resource "aws_cognito_user_pool_client" "client" {
  name             = "vpc-api-client"
  user_pool_id     = aws_cognito_user_pool.users.id
  generate_secret  = false
}

# --- Test User ---
resource "aws_cognito_user" "demo_user" {
  user_pool_id         = aws_cognito_user_pool.users.id
  username             = "testuser"
  temporary_password   = "TempPassword123!"
  force_alias_creation = true
}

# --- Cognito Authorizer ---
resource "aws_apigatewayv2_authorizer" "cognito_auth" {
  api_id           = aws_apigatewayv2_api.vpc_api.id
  name             = "CognitoAuthorizer"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.client.id]
    issuer   = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.users.id}"
  }
}

# --- Routes with Authorizer ---
resource "aws_apigatewayv2_route" "create_vpc" {
  api_id        = aws_apigatewayv2_api.vpc_api.id
  route_key     = "POST /create-vpc"
  target        = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
  authorizer_id = aws_apigatewayv2_authorizer.cognito_auth.id
}

resource "aws_apigatewayv2_route" "get_vpcs" {
  api_id        = aws_apigatewayv2_api.vpc_api.id
  route_key     = "GET /vpcs"
  target        = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
  authorizer_id = aws_apigatewayv2_authorizer.cognito_auth.id
}

# --- Lambda Permission ---
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.vpc_api.function_name
  principal     = "apigateway.amazonaws.com"
}
