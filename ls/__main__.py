import pulumi
from build_and_push import build_and_push_image
from update_lambda_and_api import update_lambda_and_create_api

# Build and push the Docker image
image, exports = build_and_push_image()

# Update Lambda function and create API Gateway
update_lambda, api, stage = update_lambda_and_create_api(image, exports)

# Export the image details
pulumi.export('image_url', image.image_name)
pulumi.export('api_url', stage.invoke_url)