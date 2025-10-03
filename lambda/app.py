import json
import boto3

ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    # Detect API Gateway payload version
    version = event.get("version")

    if version == "2.0":
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("rawPath", "")
    else:
        method = event.get("httpMethod", "")
        path = event.get("path", "")

    try:
        # GET /vpcs → List VPCs
        if method == "GET" and path.endswith("/vpcs"):
            vpcs = ec2.describe_vpcs()
            vpc_list = []
            for vpc in vpcs.get("Vpcs", []):
                name_tag = next((t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"), "")
                vpc_list.append({
                    "VpcId": vpc.get("VpcId"),
                    "Name": name_tag,
                    "CidrBlock": vpc.get("CidrBlock"),
                    "State": vpc.get("State"),
                    "IsDefault": vpc.get("IsDefault")
                })

            return {
                "statusCode": 200,
                "body": json.dumps(vpc_list)
            }

        # POST /create-vpc → Create VPC + Subnets
        elif method == "POST" and path.endswith("/create-vpc"):
            body = {}
            if event.get("body"):
                body = json.loads(event["body"])

            cidr_block = body.get("cidr_block", "10.0.0.0/16")
            name = body.get("vpc_name", "MyVPC")
            subnets_data = body.get("subnets", [])

            # Create VPC
            vpc = ec2.create_vpc(CidrBlock=cidr_block)
            vpc_id = vpc["Vpc"]["VpcId"]

            # Tag VPC
            ec2.create_tags(
                Resources=[vpc_id],
                Tags=[{"Key": "Name", "Value": name}]
            )

            # Prepare subnets
            created_subnets = []
            for i, subnet_def in enumerate(subnets_data, start=1):
                cidr = subnet_def.get("cidr_block")
                az = subnet_def.get("availability_zone")

                subnet = ec2.create_subnet(
                    VpcId=vpc_id,
                    CidrBlock=cidr,
                    AvailabilityZone=az
                )

                subnet_id = subnet["Subnet"]["SubnetId"]

                # Tag Subnet
                ec2.create_tags(
                    Resources=[subnet_id],
                    Tags=[{"Key": "Name", "Value": f"{name}-subnet-{i}"}]
                )

                created_subnets.append({
                    "SubnetId": subnet_id,
                    "CidrBlock": cidr,
                    "AvailabilityZone": az
                })

            return {
                "statusCode": 201,
                "body": json.dumps({
                    "message": "VPC and Subnets created",
                    "VpcId": vpc_id,
                    "Name": name,
                    "CidrBlock": cidr_block,
                    "Subnets": created_subnets
                })
            }

        else:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "Route not found",
                    "debug_path": path,
                    "debug_method": method
                })
            }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
