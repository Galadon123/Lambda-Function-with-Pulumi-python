import pulumi
import pulumi_aws as aws
import json
import base64
import pulumi_docker as docker
import time

# Create VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Create Internet Gateways
igw = aws.ec2.InternetGateway("my-vpc-igw",
                              vpc_id=vpc.id,
                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                              tags={"Name": "my-vpc-igw"})

# Create Route Table for Public
public_route_table = aws.ec2.RouteTable("my-vpc-public-rt",
                                        vpc_id=vpc.id,
                                        routes=[{
                                            "cidr_block": "0.0.0.0/0",
                                            "gateway_id": igw.id,
                                        }],
                                        opts=pulumi.ResourceOptions(depends_on=[igw]),
                                        tags={"Name": "my-vpc-public-rt"})

# Create Public Subnet within VPC
public_subnet = aws.ec2.Subnet("public-subnet",
                               vpc_id=vpc.id,
                               cidr_block="10.0.1.0/24",
                               availability_zone="us-east-1a",
                               map_public_ip_on_launch=True,
                               opts=pulumi.ResourceOptions(depends_on=[vpc]),
                               tags={"Name": "public-subnet"})

# Associate Route Table with Public Subnet
public_route_table_association = aws.ec2.RouteTableAssociation("public-subnet-association",
                                                               subnet_id=public_subnet.id,
                                                               route_table_id=public_route_table.id,
                                                               opts=pulumi.ResourceOptions(depends_on=[public_subnet, public_route_table]))

# Create Security Group for EC2 Instance
ec2_security_group = aws.ec2.SecurityGroup(
    "ec2-security-group",
    vpc_id=vpc.id,
    description="Allow all traffic",
    ingress=[
        {
            "protocol": "-1",  # All protocols
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[
        {
            "protocol": "-1",  # All protocols
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
    tags={"Name": "ec2-security-group"}
)

ec2_instance = aws.ec2.Instance("my-ec2-instance",
                                instance_type="t2.micro",
                                vpc_security_group_ids=[ec2_security_group.id],
                                subnet_id=public_subnet.id,
                                ami="ami-04a81a99f5ec58529",  # Example AMI ID, replace with your desired AMIs
                                tags={"Name": "my-ec2-instance"},
                                opts=pulumi.ResourceOptions(depends_on=[public_subnet, ec2_security_group]))

# Create Private Subnet within VPC
private_subnet = aws.ec2.Subnet("private-subnet",
                                vpc_id=vpc.id,
                                cidr_block="10.0.2.0/24",
                                availability_zone="us-east-1b",
                                map_public_ip_on_launch=False,
                                opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                tags={"Name": "private-subnet"})

# Create NAT Gateway in Public Subnet
# Allocate an Elastic IP
eip = aws.ec2.Eip("my-eip")

# Use the EIP's allocation ID for the NAT Gateway
nat_gateway = aws.ec2.NatGateway("my-nat-gateway",
                                subnet_id=public_subnet.id,
                                allocation_id=eip.id,  # Corrected to use EIP's ID
                                opts=pulumi.ResourceOptions(depends_on=[public_subnet, eip]),  # Updated dependency
                                tags={"Name": "my-nat-gateway"})

# Create Route Table for Private Subnet
private_route_table = aws.ec2.RouteTable("my-vpc-private-rt",
                                         vpc_id=vpc.id,
                                         routes=[{
                                             "cidr_block": "0.0.0.0/0",
                                             "gateway_id": nat_gateway.id,
                                         }],
                                         opts=pulumi.ResourceOptions(depends_on=[nat_gateway]),
                                         tags={"Name": "my-vpc-private-rt"})

# Associate Route Table with Private Subnet
private_route_table_association = aws.ec2.RouteTableAssociation("private-subnet-association",
                                                                subnet_id=private_subnet.id,
                                                                route_table_id=private_route_table.id,
                                                                opts=pulumi.ResourceOptions(depends_on=[private_subnet, private_route_table]))

# Create Security Group for Lambda function
lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                              vpc_id=vpc.id,
                                              description="Allow all traffic",
                                              ingress=[{
                                                  "protocol": "-1",  # All protocols
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              egress=[{
                                                  "protocol": "-1",  # All protocols
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                              tags={"Name": "lambda-security-group"})

# Create IAM Role for Lambda with trust policy
lambda_role = aws.iam.Role("lambda-role",
                           assume_role_policy="""{
                               "Version": "2012-10-17",
                               "Statement": [
                                   {
                                       "Action": "sts:AssumeRole",
                                       "Principal": {
                                           "Service": "lambda.amazonaws.com"
                                       },
                                       "Effect": "Allow",
                                       "Sid": ""
                                   }
                               ]
                           }""")

# Attach IAM Policy to Lambda Role
lambda_policy_attachment = aws.iam.RolePolicyAttachment("lambda-policy-attachment",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)

# Create IAM Policy for Lambda Role to access S3
lambda_policy = aws.iam.Policy("lambda-policy",
    policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::lambda-function-bucket-poridhi",
                    "arn:aws:s3:::lambda-function-bucket-poridhi/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:CreateNetworkInterface",
                    "ec2:DeleteNetworkInterface",
                    "ec2:DescribeNetworkInterfaces"
                ],
                "Resource": "*"
            }
        ]
    }""",
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)

# Attach IAM Policy to Lambda Role
lambda_policy_attachment_2 = aws.iam.RolePolicyAttachment("lambda-policy-attachment_2",
    role=lambda_role.name,
    policy_arn=lambda_policy.arn,
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)

repo = aws.ecr.Repository('my-app-repo',
    image_tag_mutability="MUTABLE",
    image_scanning_configuration={
        "scanOnPush": True
    },
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)

# Get repository credentials
creds = repo.registry_id.apply(
    lambda registry_id: aws.ecr.get_credentials(registry_id=registry_id)
)

decoded_creds = creds.authorization_token.apply(
    lambda token: base64.b64decode(token).decode('utf-8').split(':')
)

registry_server = creds.proxy_endpoint

# Define the ECR image name
ecr_image_name = repo.repository_url.apply(lambda url: f"{url}:latest")

# Push the Docker image to the ECR repository
image = docker.Image('nginx-ecr-image',
    image_name=ecr_image_name,
    build=docker.DockerBuildArgs(
        context=".",
        dockerfile="Dockerfile",
    ),
    registry={
        "server": registry_server,
        "username": decoded_creds.apply(lambda creds: creds[0]),
        "password": decoded_creds.apply(lambda creds: creds[1]),
    },
    opts=pulumi.ResourceOptions(depends_on=[repo]),
)

# Create Lambda function
lambda_function = aws.lambda_.Function("my-lambda-function",
    role=lambda_role.arn,
    image_uri=image.image_name,
    package_type="Image",
    timeout=400,
    memory_size=1024,
    vpc_config={
        "subnet_ids": [private_subnet.id],
        "security_group_ids": [lambda_security_group.id],
    },
    environment={
        "variables": {
            "ENV_VAR_1": "value1",
            "ENV_VAR_2": "value2",
            # Add any environment variables your Lambda function needs
        }
    },
    opts=pulumi.ResourceOptions(depends_on=[image, lambda_role, private_subnet, lambda_security_group])
)

# Create a CloudWatch Log Group for the Lambda function
log_group = aws.cloudwatch.LogGroup("lambda-log-group",
    name=lambda_function.name.apply(lambda name: f"/aws/lambda/{name}"),
    retention_in_days=14,
    opts=pulumi.ResourceOptions(depends_on=[lambda_function])
)

# Create S3 bucket
bucket = aws.s3.Bucket("lambda-function-bucket-poridhi",
    bucket="lambda-function-bucket-poridhi-fazlul",
    acl="private",
    tags={"Name": "Lambda Function Bucket"},
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)

def upload_exports_to_s3(outputs):
    # Convert outputs to JSON
    outputs_json = json.dumps(outputs, indent=2)
    
    # Create an S3 object with the JSON content
    aws.s3.BucketObject("pulumi-exports",
        bucket=bucket.id,
        key="pulumi-exports.json",
        content=outputs_json,
        content_type="application/json",
        opts=pulumi.ResourceOptions(depends_on=[bucket]),
    )

# Collect all outputs
all_outputs = {
    "vpc_id": vpc.id,
    "public_subnet_id": public_subnet.id,
    "private_subnet_id": private_subnet.id,
    "public_route_table_id": public_route_table.id,
    "private_route_table_id": private_route_table.id,
    "ec2_security_group_id": ec2_security_group.id,
    "lambda_security_group_id": lambda_security_group.id,
    "lambda_role_arn": lambda_role.arn,
    "ec2_private_ip": ec2_instance.private_ip,
    "repository_url": repo.repository_url,
    "ecr_registry_id": repo.registry_id,
    "image_id": image.image_name,
    "lambda_function_name": lambda_function.name,
    "lambda_function_arn": lambda_function.arn,
    "bucket_name": bucket.id,
}

pulumi.Output.all(**all_outputs).apply(lambda resolved: upload_exports_to_s3(resolved))
