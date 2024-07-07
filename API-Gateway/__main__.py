import pulumi
import pulumi_aws as aws
import json
# Fetch Lambda function ARN from S3
lambda_function_arn_object = aws.s3.BucketObject.get("lambda-function-arn-object",
    bucket="lambda-function-bucket-poridhi-1",
    key="lambda-function-arn.json"
)
lambda_function_arn_content = lambda_function_arn_object.content.apply(lambda content: json.loads(content)["arn"])
# Print the Lambda function ARN
pulumi.log.info(f"Lambda Function ARN: {lambda_function_arn.arn}")

# Define your API Gateway
api = aws.apigatewayv2.Api("my-api", protocol_type="HTTP")

# Define Lambda integration for API Gateway using fetched ARN
integration1 = aws.apigatewayv2.Integration("lambda-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",  # Use AWS_PROXY for Lambda integrations
    integration_uri="arn:aws:lambda:us-east-1:058264152807:function:my-lambda-function",# Access the ARN directly
    integration_method="ANY",
    payload_format_version="2.0"  # Handle POST requests
    
)

# Define routes for API Gateway
route1 = aws.apigatewayv2.Route("my-route",
    api_id=api.id,
    route_key="POST /my-lambda-function",  # Adjusted route key for POST method
    target=integration1.id,
)

route2 = aws.apigatewayv2.Route("test2-route",
    api_id=api.id,
    route_key="ANY /test2",
    target=integration1.id,
)

route3 = aws.apigatewayv2.Route("test1-route",
    api_id=api.id,
    route_key="ANY /test1",
    target=integration1.id,
)

# Export API Gateway endpoint URL
pulumi.export("api_url", api.api_endpoint)
