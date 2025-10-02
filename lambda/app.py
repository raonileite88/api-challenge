import json
import boto3

ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    print("DEBUG EVENT:", json.dumps(event, indent=2))

    # Detectar versão do payload
    version = event.get("version")

    if version == "2.0":
        # HTTP API (payload v2.0)
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("rawPath", "")
    else:
        # REST API (payload v1.0)
        method = event.get("httpMethod", "")
        path = event.get("path", "")

    print(f"DEBUG: method={method}, path={path}")

    try:
        # GET /vpcs → Listar VPCs
        if method == "GET" and path.endswith("/vpcs"):
            vpcs = ec2.describe_vpcs()
            vpc_list = []
            for vpc in vpcs.get("Vpcs", []):
                vpc_list.append({
                    "VpcId": vpc.get("VpcId"),
                    "CidrBlock": vpc.get("CidrBlock"),
                    "State": vpc.get("State"),
                    "IsDefault": vpc.get("IsDefault")
                })

            return {
                "statusCode": 200,
                "body": json.dumps(vpc_list)
            }

        # POST /create-vpc → Criar VPC + Subnets
        elif method == "POST" and path.endswith("/create-vpc"):
            body = {}
            if event.get("body"):
                body = json.loads(event["body"])

            cidr_block = body.get("cidr_block", "10.0.0.0/16")
            name = body.get("vpc_name", "MyVPC")
            subnets_data = body.get("subnets", [])

            # Criar VPC
            vpc = ec2.create_vpc(CidrBlock=cidr_block)
            vpc_id = vpc["Vpc"]["VpcId"]

            # Criar tag na VPC
            ec2.create_tags(
                Resources=[vpc_id],
                Tags=[{"Key": "Name", "Value": name}]
            )

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

                # Tag na Subnet
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
                    "CidrBlock": cidr_block,
                    "Subnets": created_subnets
                })
            }

        else:
            print(f"Route not found: method={method}, path={path}")
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
