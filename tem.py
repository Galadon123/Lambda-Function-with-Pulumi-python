import pulumi
import pulumi_aws as aws

# Existing VPC, Subnet, Security Group, IAM Role, and ECR Repository setup...

# Define the API Gateway
api_gateway = aws.apigatewayv2.Api("my-api",
    protocol_type="HTTP",
    tags={"Name": "my-api"})

# Define the API Gateway Integration for Lambda
integration = aws.apigatewayv2.Integration("my-integration",
    api_id=api_gateway.id,
    integration_type="AWS_PROXY",
    integration_uri=pulumi.Output.concat("arn:aws:apigateway:", pulumi.get_stack().region, ":lambda:path/2015-03-31/functions/", "arn:aws:lambda:", pulumi.get_stack().region, ":", pulumi.get_stack().account_id, ":function:my-lambda-function/invocations"),
    payload_format_version="2.0")

# Define the default route
default_route = aws.apigatewayv2.Route("default-route",
    api_id=api_gateway.id,
    route_key="ANY /{proxy+}",
    target=pulumi.Output.concat("integrations/", integration.id))

# Define a deployment for the API
deployment = aws.apigatewayv2.Deployment("my-deployment",
    api_id=api_gateway.id,
    opts=pulumi.ResourceOptions(depends_on=[default_route]))

# Define a stage for the API
stage = aws.apigatewayv2.Stage("my-stage",
    api_id=api_gateway.id,
    deployment_id=deployment.id,
    name="default",
    auto_deploy=True)

# Add permissions for API Gateway to invoke the Lambda function
lambda_permission = aws.lambda_.Permission("apigateway-lambda-permission",
    action="lambda:InvokeFunction",
    function="my-lambda-function",
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat("arn:aws:execute-api:", pulumi.get_stack().region, ":", pulumi.get_stack().account_id, ":", api_gateway.id, "/*/*"))

# Export the API Gateway URL
pulumi.export("api_endpoint", pulumi.Output.concat("https://", api_gateway.id, ".execute-api.", pulumi.get_stack().region, ".amazonaws.com/", stage.name))
