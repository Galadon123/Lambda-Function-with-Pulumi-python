import pulumi
import pulumi_aws as aws
import json

# Define the bucket and object names
bucket_name = "lambda-function-bucket-poridhi-1"
object_key = "lambda-function-arn.json"

# Fetch the object from S3
bucket_object = aws.s3.get_object(bucket=bucket_name, key=object_key)

# Define a function to parse the ARN from the bucket object content
def get_lambda_function_arn(content):
    arn = json.loads(content).get("arn")
    if arn is None:
        raise ValueError("ARN not found in the bucket object content")
    return arn

# Extract the ARN from the bucket object's body directly
lambda_function_arn = pulumi.Output.from_input(bucket_object.body).apply(get_lambda_function_arn)

pulumi.export("lambda_function_arn", lambda_function_arn)

# Create API Gateway
api = aws.apigatewayv2.Api("my-api", protocol_type="HTTP")

# Define Lambda integration for API Gateway using fetched ARN
integration = pulumi.Output.from_input(lambda_function_arn).apply(lambda arn: aws.apigatewayv2.Integration("lambda-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",  # Use AWS_PROXY for Lambda integrations
    integration_uri=arn,
    integration_method="ANY",
    payload_format_version="2.0"
))

# Define routes for API Gateway
route1 = aws.apigatewayv2.Route("my-route",
    api_id=api.id,
    route_key="ANY /my-lambda-function",  # Adjusted route key for POST methods
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
stage = aws.apigatewayv2.Stage("default-stage",
    api_id=api.id,
    auto_deploy=True  # Automatically deploy changes to this stage
)

# Export API Gateway endpoint URL
lambda_trigger = aws.lambda_.FunctionEventInvokeConfig("lambda-trigger",
    function_name="my-lambda-function",  # Specify your existing Lambda function name here
    destination_config={
        "onSuccess": {
            "destination": lambda_function_arn  # Use the Lambda function ARN as the destination
        }
    },
)