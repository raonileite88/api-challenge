# AWS Lambda VPC Management API

## Project Overview

This project provides a serverless API using **AWS Lambda** and **API Gateway** to **create and list VPCs** in your AWS account.
It is designed to be lightweight and scalable, using **Python 3.11** as the runtime for the Lambda function.
The project also integrates **AWS Cognito** for authentication using JWT tokens.

The API exposes two main endpoints:

1. `GET /vpcs` - List all VPCs in the AWS account.
2. `POST /create-vpc` - Create a new VPC with one or more subnets.

---

## Architecture

* **AWS Lambda:** Contains the Python code that handles the API requests and interacts with AWS VPC service.
* **API Gateway:** Exposes HTTP endpoints that trigger the Lambda function.
* **AWS Cognito:** Handles authentication and issues JWT tokens for API access.
* **CloudWatch Logs:** Stores logs from the Lambda function (for debugging purposes).

---

## Prerequisites

Before using the API, ensure the following:

* An AWS account with **VPC permissions** (`ec2:DescribeVpcs`, `ec2:CreateVpc`, `ec2:CreateSubnet`, etc.).
* **AWS CLI** installed and configured with your credentials.
* Python 3.11 runtime for Lambda.

---

## AWS Cognito JWT Authentication

The API requires a **JWT token** from Cognito to authorize requests.

You can get a JWT token using the AWS CLI:

```bash
aws cognito-idp admin-initiate-auth \
  --region <your-region> \
  --user-pool-id <your-user-pool-id> \
  --client-id <your-app-client-id> \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters "USERNAME=<username>,PASSWORD=<password>"
```

Replace:

* `<your-region>` with your AWS region (e.g., `us-east-1`)
* `<your-user-pool-id>` with your Cognito User Pool ID
* `<your-app-client-id>` with your App Client ID
* `<username>` and `<password>` with your Cognito user credentials

The output will include an **IdToken** which you can use in the `Authorization` header for API requests:

```
Authorization: <JWT_TOKEN>
```

---

## API Endpoints

### 1. GET /vpcs

Retrieve a list of all VPCs in your AWS account.

**Request:**

```bash
curl -X GET "https://<api-gateway-url>/prod/vpcs" \
  -H "Authorization: <JWT_TOKEN>"
```

**Response:**

```json
[
  {
    "vpc_id": "vpc-0123456789abcdef0",
    "cidr_block": "10.0.0.0/16",
    "is_default": false,
    "subnets": [
      {
        "subnet_id": "subnet-11111111",
        "name": "SubnetA",
        "cidr_block": "10.0.1.0/24",
        "availability_zone": "us-east-1a"
      }
    ]
  }
]
```

---

### 2. POST /create-vpc

Create a new VPC with optional subnets.

**Request:**

```bash
curl -X POST "https://<api-gateway-url>/prod/create-vpc" \
  -H "Authorization: <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
        "vpc_name": "MyVPC",
        "cidr_block": "10.0.0.0/16",
        "subnets": [
          {
            "name": "SubnetA",
            "cidr_block": "10.0.1.0/24",
            "az": "us-east-1a"
          },
          {
            "name": "SubnetB",
            "cidr_block": "10.0.2.0/24",
            "az": "us-east-1b"
          }
        ]
      }'
```

**Response:**

```json
{
  "vpc_id": "vpc-0123456789abcdef0",
  "cidr_block": "10.0.0.0/16",
  "subnets": [
    {
      "subnet_id": "subnet-11111111",
      "name": "SubnetA",
      "cidr_block": "10.0.1.0/24",
      "availability_zone": "us-east-1a"
    },
    {
      "subnet_id": "subnet-22222222",
      "name": "SubnetB",
      "cidr_block": "10.0.2.0/24",
      "availability_zone": "us-east-1b"
    }
  ]
}
```

---

## Notes

* Ensure that your **JWT token** is valid and included in the `Authorization` header for all API requests.
* CloudWatch logs are available for debugging, but you may disable or remove debug logs in production to avoid excessive logging.
* The Lambda function is designed to handle **JSON input/output**.

---

## Example Workflow

1. Obtain JWT token from Cognito.
2. Call `GET /vpcs` to see existing VPCs.
3. Call `POST /create-vpc` to create a new VPC.
4. Verify the creation by calling `GET /vpcs` again.

---

## License

This project is provided as-is for educational and internal use. No warranty is provided.
