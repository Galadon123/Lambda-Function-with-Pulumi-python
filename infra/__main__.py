import pulumi
import pulumi_aws as aws
import json
import base64
import pulumi_docker as docker

def get_exports_from_s3(bucket_name, object_key):
    # Use the get_object function to retrieve the S3 object
    s3_object = aws.s3.get_object(bucket=bucket_name, key=object_key)
    
    # Check if s3_object.body is a string or an Output
    if isinstance(s3_object.body, str):
        # If it's a string, parse it and wrap it in a Pulumi Output
        return pulumi.Output.from_input(json.loads(s3_object.body))
    else:
        # If it's an Output, apply json.loads to it
        return s3_object.body.apply(lambda body: json.loads(body))

# Usage
exports = get_exports_from_s3('lambda-function-bucket-poridhi', 'pulumi-exports.json')

# Get ECR repository details from exports
repository_url = exports.apply(lambda exp: exp['repository_url'])
ecr_registry_id = exports.apply(lambda exp: exp['ecr_registry_id'])

# Get repository credentials
creds = aws.ecr.get_credentials_output(registry_id=ecr_registry_id)

decoded_creds = creds.authorization_token.apply(
    lambda token: base64.b64decode(token).decode('utf-8').split(':')
)

registry_server = creds.proxy_endpoint

# Define the ECR image name
ecr_image_name = repository_url.apply(lambda url: f"{url}:latest")

# Push the Docker image to the ECR repository
image = docker.Image('my-node-app',
    image_name=ecr_image_name,
    build=docker.DockerBuildArgs(
        context=".",
        dockerfile="Dockerfile",
    ),
    registry={
        "server": registry_server,
        "username": decoded_creds.apply(lambda creds: creds[0]),
        "password": decoded_creds.apply(lambda creds: creds[1]),
    }
)

# lambda_function_name = exports.apply(lambda exp: exp['lambda_function_name'])
# lambda_role_arn = exports.apply(lambda exp: exp['lambda_role_arn'])
# lambda_function_arn = exports.apply(lambda exp: exp['lambda_function_arn'])

# # Retrieve the existing Lambda function resource
# existing_lambda_function = lambda_function_arn.apply(lambda arn: aws.lambda_.Function.get("existing-lambda-function", arn))

# lambda_function = aws.lambda_.Function.get("existing-lambda-function", existing_lambda_function.value())

# # Update the actual function resource
# lambda_function.update(
#     opts=pulumi.ResourceOptions(
#         replace_on_changes=["image_uri"],
#         delete_before_replace=False,
#     ),
#     image_uri=image.image_name,
# )

# Export the image details
pulumi.export('image_url', image.image_name)



