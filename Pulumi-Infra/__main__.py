import pulumi
import pulumi_aws as aws

# Create a VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Create a private subnet
private_subnet = aws.ec2.Subnet("private-subnet",
                                vpc_id=vpc.id,
                                cidr_block="10.0.1.0/24",
                                availability_zone="us-east-1a",
                                tags={"Name": "private-subnet"})

# Create an ECR repository
ecr_repo = aws.ecr.Repository("my-lambda-function",
                              image_scanning_configuration={"scanOnPush": True},
                              tags={"Name": "my-lambda-function"})

# Create an IAM role for Lambda
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

lambda_policy = aws.iam.RolePolicy("lambda-policy",
                                   role=lambda_role.id,
                                   policy="""{
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
                                   }""")

# Create a security group for Lambda
lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                              vpc_id=vpc.id,
                                              egress=[{
                                                  "protocol": "-1",
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              tags={"Name": "lambda-security-group"})

# Export the VPC ID, Subnet ID, Security Group ID, ECR Repository URL, and Lambda Role ARN
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("ecr_registry_id", ecr_repo.registry_id)
pulumi.export("lambda_role_arn", lambda_role.arn)
pulumi.export("lambda_security_group_id", lambda_security_group.id)
