import json
import boto3

def lambda_handler(event, context):
    # Debug: logar o evento inteiro
    print("DEBUG FULL EVENT:")
    print(json.dumps(event, indent=2))

    # Extrair method e path (REST API v1 usa essas chaves)
    method = event.get("httpMethod", "")
    path = event.get("path", "")

    print(f"DEBUG: method={method}, path={path}")

    # Rotas
    if method == "GET" and path == "/prod/vpcs":
        # Aqui você pode buscar as VPCs do boto3 se quiser
        return {
            "statusCode": 200,
            "body": json.dumps([])
        }

    elif method == "POST" and path == "/prod/create-vpc":
        body = event.get("body")
        if body:
            try:
                data = json.loads(body)
            except Exception as e:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": f"Invalid JSON: {str(e)}"})
                }
        else:
            data = {}

        # Exemplo: criar VPC fictícia (só resposta de teste)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "msg": "VPC created",
                "input": data
            })
        }

    else:
        # Rota não encontrada
        print(f"Route not found: method={method}, path={path}")
        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Route not found",
                "debug_path": path,
                "debug_method": method
            })
        }
