import pulumi
import pulumi_aws as aws

# Hardcoded ARN for the Lambda function
lambda_function_arn = "arn:aws:lambda:us-east-1:058264152807:function:my-lambda-function"

# Define your API Gateway
api = aws.apigatewayv2.Api("my-api", protocol_type="HTTP")

# Define Lambda integration for API Gateway using hardcoded ARN
integration = aws.apigatewayv2.Integration("lambda-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",  # Use AWS_PROXY for Lambda integrations
    integration_uri=lambda_function_arn,
    integration_method="ANY",
    payload_format_version="2.0"
)

# Define routes for API Gateway
route1 = aws.apigatewayv2.Route("my-route",
    api_id=api.id,
    route_key="ANY /my-lambda-function",  # Adjusted route key for POST method
    target=integration.id.apply(lambda id: f"integrations/{id}")
)

route2 = aws.apigatewayv2.Route("test2-route",
    api_id=api.id,
    route_key="ANY /my-lambda-function/test2",
    target=integration.id.apply(lambda id: f"integrations/{id}")
)

route3 = aws.apigatewayv2.Route("test1-route",
    api_id=api.id,
    route_key="ANY /my-lambda-function/test1",
    target=integration.id.apply(lambda id: f"integrations/{id}")
)

# Export API Gateway endpoint URL
pulumi.export("api_url", api.api_endpoint)
