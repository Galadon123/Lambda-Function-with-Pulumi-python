import pulumi
import pulumi_aws as aws
import subprocess
import time

# Custom resource provider for updating the Lambda function
class LambdaUpdater(pulumi.dynamic.ResourceProvider):
    def create(self, props):
        return self.update(None, props)

    def update(self, _id, props, olds=None):
        # Construct the AWS CLI command to update the Lambda function code
        cmd = f"aws lambda update-function-code --function-name {props['function_name']} --image-uri {props['image_uri']} --region {props['region']}"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return pulumi.dynamic.UpdateResult(outs=props)

# Custom resource for updating the Lambda function
class LambdaUpdate(pulumi.dynamic.Resource):
    def __init__(self, name, props, opts=None):
        super().__init__(LambdaUpdater(), name, props, opts)

# Function to update the Lambda function and create the API Gateway
def update_lambda_and_create_api(image, exports):
    # Extract required values from the exports
    lambda_function_name = exports.apply(lambda exp: exp['lambda_function_name'])
    lambda_role_arn = exports.apply(lambda exp: exp['lambda_role_arn'])
    lambda_function_arn = exports.apply(lambda exp: exp['lambda_function_arn'])

    # Update the Lambda function
    update_lambda = LambdaUpdate('update-lambda-function',
        {
            'function_name': lambda_function_name,
            'image_uri': image.image_name,
            'region': aws.config.region,
            'timestamp': str(time.time())
        },
        opts=pulumi.ResourceOptions(depends_on=[image])
    )

    # Create the API Gateway
    api = aws.apigateway.RestApi("myApi",
        description="API Gateway for Lambda function",
    )

    # Create resources and methods for the API Gateway
    default_resource = aws.apigateway.Resource("defaultResource",
        parent_id=api.root_resource_id,
        path_part="default",
        rest_api=api.id,
    )
    lambda_resource = aws.apigateway.Resource("lambdaResource",
        parent_id=default_resource.id,
        path_part="my-lambda-function",
        rest_api=api.id,
    )
    test1_resource = aws.apigateway.Resource("test1Resource",
        parent_id=lambda_resource.id,
        path_part="test1",
        rest_api=api.id,
    )
    test2_resource = aws.apigateway.Resource("test2Resource",
        parent_id=lambda_resource.id,
        path_part="test2",
        rest_api=api.id,
    )
    test1_method = aws.apigateway.Method("test1_Method",
        http_method="GET",
        authorization="NONE",
        resource_id=test1_resource.id,
        rest_api=api.id,
    )
    test2_method = aws.apigateway.Method("test2_Method",
        http_method="GET",
        authorization="NONE",
        resource_id=test2_resource.id,
        rest_api=api.id,
    )

    # Create a method for the GET request
    method = aws.apigateway.Method("myMethod",
        http_method="GET",
        authorization="NONE",
        resource_id=lambda_resource.id,
        rest_api=api.id,
    )

    # Create integrations for the methods
    integration = aws.apigateway.Integration("myIntegration",
        http_method=method.http_method,
        integration_http_method="POST",
        type="AWS_PROXY",
        uri=lambda_function_arn.apply(lambda arn: f"arn:aws:apigateway:{aws.config.region}:lambda:path/2015-03-31/functions/{arn}/invocations"),
        resource_id=lambda_resource.id,
        rest_api=api.id,
    )
    test1_integration = aws.apigateway.Integration("test1Integration",
        http_method=test1_method.http_method,
        integration_http_method="POST",
        type="AWS_PROXY",
        uri=lambda_function_arn.apply(lambda arn: f"arn:aws:apigateway:{aws.config.region}:lambda:path/2015-03-31/functions/{arn}/invocations"),
        resource_id=test1_resource.id,
        rest_api=api.id,
    )
    test2_integration = aws.apigateway.Integration("test2Integration",
        http_method=test2_method.http_method,
        integration_http_method="POST",
        type="AWS_PROXY",
        uri=lambda_function_arn.apply(lambda arn: f"arn:aws:apigateway:{aws.config.region}:lambda:path/2015-03-31/functions/{arn}/invocations"),
        resource_id=test2_resource.id,
        rest_api=api.id,
    )

    # Grant API Gateway permission to invoke the Lambda function
    permission = aws.lambda_.Permission("myPermission",
        action="lambda:InvokeFunction",
        function=lambda_function_arn,
        principal="apigateway.amazonaws.com",
        source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*"),
    )

    # Deploy the API
    deployment = aws.apigateway.Deployment("myDeployment",
        rest_api=api.id,
        triggers={
            "integration": integration.id,
            "test1_integration": test1_integration.id,
            "test2_integration": test2_integration.id,
        },
        opts=pulumi.ResourceOptions(depends_on=[integration, test1_integration, test2_integration]),
    )

    # Create a stage
    stage = aws.apigateway.Stage("myStage",
        deployment=deployment.id,
        rest_api=api.id,
        stage_name="prod",
    )

    return update_lambda, api, stage
