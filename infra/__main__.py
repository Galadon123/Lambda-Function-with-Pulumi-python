import pulumi
import pulumi_aws as aws
import json

# Create a VPC with a specified CIDR block
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Create a private subnet within the VPC
private_subnet = aws.ec2.Subnet("private-subnet",
                                vpc_id=vpc.id,
                                cidr_block="10.0.1.0/24",
                                availability_zone="us-east-1a",
                                tags={"Name": "private-subnet"})

# Create an ECR repository with image scanning enabled on push
ecr_repo = aws.ecr.Repository("my-lambda-function",
                              image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                                  scan_on_push=True),
                              tags={"Name": "my-lambda-function"})

# IAM role for Lambda with an assume role policy allowing Lambda service
assume_role_policy = json.dumps({
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
})

lambda_role = aws.iam.Role("lambda-role",
                           assume_role_policy=assume_role_policy)

# Attach a policy to the Lambda role that allows necessary actions
lambda_policy = aws.iam.RolePolicy("lambda-policy",
                                   role=lambda_role.id,
                                   policy=json.dumps({
                                       "Version": "2012-10-17",
                                       "Statement": [
                                           {
                                               "Effect": "Allow",
                                               "Action": [
                                                   "logs:CreateLogGroup",
                                                   "logs:CreateLogStream",
                                                   "logs:PutLogEvents"
                                               ],
                                               "Resource": "arn:aws:logs:*:*:*"
                                           },
                                           {
                                               "Effect": "Allow",
                                               "Action": [
                                                   "ecr:GetDownloadUrlForLayer",
                                                   "ecr:BatchGetImage",
                                                   "ecr:BatchCheckLayerAvailability"
                                               ],
                                               "Resource": "*"
                                           },
                                           {
                                               "Effect": "Allow",
                                               "Action": [
                                                   "ec2:CreateNetworkInterface",
                                                   "ec2:DescribeNetworkInterfaces",
                                                   "ec2:DeleteNetworkInterface"
                                               ],
                                               "Resource": "*"
                                           }
                                       ]
                                   }))

# Create a security group for Lambda functions within the VPC
lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                              vpc_id=vpc.id,
                                              egress=[{
                                                  "protocol": "-1",
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              tags={"Name": "lambda-security-group"})

# Export the VPC ID, Subnet ID, ECR Repository URL, and Lambda Security Group ID
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("lambda_security_group_id", lambda_security_group.id)
