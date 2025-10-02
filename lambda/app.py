import json
import boto3
import os
from datetime import datetime

# --- AWS clients ---
ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # --- DEBUG: log the incoming event ---
    print("DEBUG FULL EVENT:")
    print(json.dumps(event, indent=2))

    # --- Extract HTTP method and path ---
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')

    print(f"DEBUG: method={method}, path={path}")

    # --- Define full paths including stage ---
    routes = {
        "GET": ["/prod/vpcs"],
        "POST": ["/prod/create-vpc"]
    }

    # --- Handle GET /prod/vpcs ---
    if method == "GET" and path == "/prod/vpcs":
        try:
            response = table.scan()
            return {
                'statusCode': 200,
                'body': json.dumps(response.get('Items', []))
            }
        except Exception as e:
            print(f"Error in GET {path}: {e}")
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

    # --- Handle POST /prod/create-vpc ---
    elif method == "POST" and path == "/prod/create-vpc":
        try:
            body = json.loads(event.get('body', '{}'))
            vpc_name = body.get('vpc_name')
            cidr_block = body.get('cidr_block')
            subnets = body.get('subnets', [])

            # Create VPC
            vpc_resp = ec2.create_vpc(CidrBlock=cidr_block)
            vpc_id = vpc_resp['Vpc']['VpcId']

            # Add Name tag to VPC
            ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_name}])

            # Create subnets
            subnets_info = []
            for sn in subnets:
                subnet_resp = ec2.create_subnet(
                    VpcId=vpc_id,
                    CidrBlock=sn['cidr_block'],
                    AvailabilityZone=sn['az']
                )
                subnet_id = subnet_resp['Subnet']['SubnetId']
                ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': sn['name']}])
                subnets_info.append({
                    'subnet_id': subnet_id,
                    'name': sn['name'],
                    'az': sn['az'],
                    'cidr_block': sn['cidr_block']
                })

            # Save to DynamoDB
            table.put_item(Item={
                'vpc_id': vpc_id,
                'vpc_name': vpc_name,
                'cidr_block': cidr_block,
                'subnets': subnets_info,
                'created_at': datetime.utcnow().isoformat()
            })

            return {
                'statusCode': 200,
                'body': json.dumps({'vpc_id': vpc_id, 'subnets': subnets_info})
            }

        except Exception as e:
            print(f"Error in POST {path}: {e}")
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

    # --- Invalid route ---
    else:
        print(f"Route not found: method={method}, path={path}")
        return {'statusCode': 404, 'body': json.dumps({'error': 'Route not found', 'debug_path': path})}
