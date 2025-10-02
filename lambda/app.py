import json
import boto3

ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    print("DEBUG EVENT:", json.dumps(event, indent=2))

    # Extrair método e path do API Gateway v2 (HTTP API)
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")

    print(f"DEBUG: method={method}, path={path}")

    try:
        if method == "GET" and path == "/prod/vpcs":
            # Listar VPCs
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

        elif method == "POST" and path == "/prod/create-vpc":
            # Criar VPC
            body = {}
            if event.get("body"):
                body = json.loads(event["body"])

            cidr_block = body.get("CidrBlock", "10.0.0.0/16")  # Default se não enviar nada
            vpc = ec2.create_vpc(CidrBlock=cidr_block)

            # Adiciona tag Name
            ec2.create_tags(
                Resources=[vpc["Vpc"]["VpcId"]],
                Tags=[{"Key": "Name", "Value": body.get("Name", "MyVPC")}]
            )

            return {
                "statusCode": 201,
                "body": json.dumps({
                    "message": "VPC created",
                    "VpcId": vpc["Vpc"]["VpcId"],
                    "CidrBlock": vpc["Vpc"]["CidrBlock"]
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
