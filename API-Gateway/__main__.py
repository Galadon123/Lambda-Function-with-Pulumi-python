import pulumi
import pulumi_aws as aws
import json

# Define the S3 bucket and object keys
bucket_name = "lambda-function-bucket-poridhi-1"
object_key = "lambda-function-arn.json"

# Fetch the S3 object
s3_object = aws.s3.BucketObject("lambda-function-arn-object",
    bucket=bucket_name,
    key=object_key)

# Function to extract the ARN from the object content
def extract_arn(content):
    data = json.loads(content)
    return data["arn"]

# Get the object content as a string and parse the ARN
lambda_function_arn = s3_object.content.apply(extract_arn)

# Define your API Gateway
api = aws.apigatewayv2.Api("my-api", protocol_type="HTTP")

# Define Lambda integration for API Gateway using fetched ARN
integration = lambda_function_arn.apply(lambda arn: aws.apigatewayv2.Integration("lambda-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",  # Use AWS_PROXY for Lambda integrations
    integration_uri=arn,
    integration_method="ANY",
    payload_format_version="2.0"
))

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
