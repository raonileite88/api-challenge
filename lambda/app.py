import json
import boto3
import os
from datetime import datetime

# AWS clients
ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Extract method and path from API Gateway HTTP API v2 event
    method = event.get("requestContext", {}).get("http", {}).get("method")
    raw_path = event.get("rawPath", "")

    # Remove stage prefix if present (e.g., /prod/vpcs -> /vpcs)
    parts = raw_path.split("/", 2)
    path = "/" + parts[2] if len(parts) > 2 else raw_path

    print("DEBUG Method:", method)
    print("DEBUG RawPath:", raw_path)
    print("DEBUG Normalized Path:", path)

    # --- POST /create-vpc ---
    if method == "POST" and path == "/create-vpc":
        try:
            body = json.loads(event.get("body", "{}"))
            vpc_name = body.get("vpc_name")
            cidr_block = body.get("cidr_block")
            subnets = body.get("subnets", [])

            # Create VPC
            vpc_resp = ec2.create_vpc(CidrBlock=cidr_block)
            vpc_id = vpc_resp["Vpc"]["VpcId"]

            # Add Name tag to VPC
            ec2.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": vpc_name}])

            # Create subnets
            subnets_info = []
            for sn in subnets:
                subnet_resp = ec2.create_subnet(
                    VpcId=vpc_id,
                    CidrBlock=sn["cidr_block"],
                    AvailabilityZone=sn["az"]
                )
                subnet_id = subnet_resp["Subnet"]["SubnetId"]
                ec2.create_tags(Resources=[subnet_id], Tags=[{"Key": "Name", "Value": sn["name"]}])
                subnets_info.append({
                    "subnet_id": subnet_id,
                    "name": sn["name"],
                    "az": sn["az"],
                    "cidr_block": sn["cidr_block"]
                })

            # Save VPC information in DynamoDB
            table.put_item(Item={
                "vpc_id": vpc_id,
                "vpc_name": vpc_name,
                "cidr_block": cidr_block,
                "subnets": subnets_info,
                "created_at": datetime.utcnow().isoformat()
            })

            return {
                "statusCode": 200,
                "body": json.dumps({"vpc_id": vpc_id, "subnets": subnets_info})
            }

        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    # --- GET /vpcs ---
    elif method == "GET" and path == "/vpcs":
        try:
            response = table.scan()
            return {
                "statusCode": 200,
                "body": json.dumps(response["Items"])
            }
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    # --- Invalid route ---
    else:
        return {"statusCode": 404, "body": json.dumps({"error": "Route not found", "debug_path": path})}
