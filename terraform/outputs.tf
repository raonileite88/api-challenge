output "lambda_name" {
  value = aws_lambda_function.vpc_api.function_name
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.vpc_api.api_endpoint
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.users.id
}

output "cognito_user_pool_client_id" {
  value = aws_cognito_user_pool_client.client.id
}
