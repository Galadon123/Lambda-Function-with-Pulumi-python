import pulumi
import pulumi_aws as aws

# Fetch Lambda function ARN from S3
lambda_function_arn = pulumi.Output.from_input(
    aws.s3.get_object(bucket="lambda-function-bucket-poridhi", key="lambda-function-arn.json")
).apply(lambda obj: obj["Body"].read().decode("utf-8"))

# Define your API Gateway
api = aws.apigatewayv2.Api("my-api", protocol_type="HTTP", target="AWS_LAMBDA", tags={"Name": "my-api"})

# Define Lambda integration for API Gateway using fetched ARN
integration1 = aws.apigatewayv2.Integration("lambda-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",
    integration_method="POST",
    integration_uri=lambda_function_arn,
    integration_timeout_milliseconds=3000,
    payload_format_version="2.0",
    tags={"Name": "lambda-integration"},
)

# Define routes for API Gateway
route1 = aws.apigatewayv2.Route("my-route",
    api_id=api.id,
    route_key="ANY /my-lambda-function",
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
