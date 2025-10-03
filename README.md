# VPC Management API

This project provides a serverless HTTP API to **create and list VPCs and subnets** in AWS using **Lambda**, **API Gateway**, and **Cognito JWT authentication**. The API is protected by a Cognito User Pool, and all requests require a valid JWT token.

---

## Table of Contents

* [Architecture](#architecture)
* [API Endpoints](#api-endpoints)
* [Authentication](#authentication)
* [Creating a Cognito User](#creating-a-cognito-user)
* [Getting a JWT Token](#getting-a-jwt-token)
* [Usage](#usage)

---

## Architecture

* **Lambda function** handles all API requests:

  * `GET /vpcs` → Lists all VPCs.
  * `POST /create-vpc` → Creates a new VPC with subnets.
* **API Gateway (HTTP API)** routes requests to the Lambda.
* **Cognito User Pool** handles user authentication.
* **JWT Authorizer** ensures only authorized users can access the API.

---

## API Usage

Use the `IdToken` from Cognito in the `Authorization` header.

### Get VPCs

```bash
curl -X GET https://<API_GATEWAY_URL>/vpcs \
  -H "Authorization: <JWT_ID_TOKEN>"
```

**Response:**

```json
[
  {
    "VpcId": "vpc-123456",
    "CidrBlock": "10.0.0.0/16",
    "Name": "MyVPC",
    "State": "available",
    "IsDefault": false
  }
]
```

### Create VPC

```bash
curl -X POST https://<API_GATEWAY_URL>/create-vpc \
  -H "Authorization: <JWT_ID_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "vpc_name": "MyVPC",
    "cidr_block": "10.0.0.0/16",
    "subnets": [
      {"name": "SubnetA", "cidr_block": "10.0.1.0/24", "az": "us-east-1a"},
      {"name": "SubnetB", "cidr_block": "10.0.2.0/24", "az": "us-east-1b"}
    ]
  }'
```

**Response:**

```json
{
  "message": "VPC and Subnets created",
  "VpcId": "vpc-123456",
  "CidrBlock": "10.0.0.0/16",
  "Name": "MyVPC",
  "Subnets": [
    {"SubnetId": "subnet-111", "CidrBlock": "10.0.1.0/24", "AvailabilityZone": "us-east-1a"},
    {"SubnetId": "subnet-222", "CidrBlock": "10.0.2.0/24", "AvailabilityZone": "us-east-1b"}
  ]
}
```

---

## Authentication

All requests require a **JWT token** obtained from AWS Cognito. The API Gateway JWT authorizer validates this token automatically.

---

## Creating a Cognito User

You can create a user manually using the **AWS CLI**. Replace `YOUR_USER_POOL_ID` and `USERNAME` with your values. The temporary password will need to be changed at first login.

```bash
aws cognito-idp admin-create-user \
  --user-pool-id YOUR_USER_POOL_ID \
  --username testuser \
  --temporary-password "TempPassword123!" \
  --message-action "SUPPRESS"
```

* `--message-action "SUPPRESS"` prevents sending a welcome email.
* After creation, the user must **set a permanent password** via the AWS Console or CLI (`admin-set-user-password`).

---

## Getting a JWT Token

Once the user exists, you can get a JWT token using:

```bash
aws cognito-idp admin-initiate-auth \
  --region us-east-1 \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_USER_POOL_CLIENT_ID \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters "USERNAME=testuser,PASSWORD=YourPassword123!"
```

This will return a JSON containing `IdToken`, `AccessToken`, and `RefreshToken`. Use the `IdToken` in the `Authorization` header for API requests:

```
Authorization: Bearer <ID_TOKEN>
```

---

## Usage

1. Deploy the API using Terraform.
2. Create a Cognito user using AWS CLI.
3. Get a JWT token.
4. Use the token to call the API via tools like **Insomnia**, **Postman**, or `curl`.

Example with `curl`:

```bash
curl -H "Authorization: Bearer <ID_TOKEN>" https://your-api.execute-api.us-east-1.amazonaws.com/prod/vpcs
```

---

**Security Note:**
Do **not** hardcode users or passwords in Terraform. Always create users securely via CLI, Console, or an external system.
