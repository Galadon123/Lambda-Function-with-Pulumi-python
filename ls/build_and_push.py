import pulumi
import pulumi_aws as aws
import json
import base64
import pulumi_docker as docker

def get_exports_from_s3(bucket_name, object_key):
    s3_object = aws.s3.get_object(bucket=bucket_name, key=object_key)
    
    if isinstance(s3_object.body, str):
        return pulumi.Output.from_input(json.loads(s3_object.body))
    else:
        return s3_object.body.apply(lambda body: json.loads(body))

def build_and_push_image():
    exports = get_exports_from_s3('lambda-function-bucket-poridhi-fazlul', 'pulumi-exports.json')

    repository_url = exports.apply(lambda exp: exp['repository_url'])
    ecr_registry_id = exports.apply(lambda exp: exp['ecr_registry_id'])

    creds = aws.ecr.get_credentials_output(registry_id=ecr_registry_id)

    decoded_creds = creds.authorization_token.apply(
        lambda token: base64.b64decode(token).decode('utf-8').split(':')
    )

    registry_server = creds.proxy_endpoint

    ecr_image_name = repository_url.apply(lambda url: f"{url}:latest")

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

    return image, exports