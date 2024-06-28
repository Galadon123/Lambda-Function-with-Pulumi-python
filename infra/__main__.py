import pulumi
import pulumi_aws as aws
import json

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
ecr_repo = aws.ecr.Repository("my-ecr-repo",
                              image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                                  scan_on_push=True),
                              tags={"Name": "my-ecr-repo"})

# Create an IAM role for Lambda
assume_role_policy = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Action": "sts:AssumeRole",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
    }]
})

lambda_role = aws.iam.Role("lambda-role",
                           assume_role_policy=assume_role_policy)

# Attach the AWS managed ECR power user policy to the IAM role
managed_policy_attachment = aws.iam.RolePolicyAttachment("lambda-role-ecr-poweruser",
                                                        role=lambda_role.name,
                                                        policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser")

# Create a security group for Lambda
lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                              vpc_id=vpc.id,
                                              egress=[aws.ec2.SecurityGroupEgressArgs(
                                                  protocol="-1",
                                                  from_port=0,
                                                  to_port=0,
                                                  cidr_blocks=["0.0.0.0/0"],
                                              )],
                                              tags={"Name": "lambda-security-group"})

# Export the VPC ID, Subnet ID, ECR Repository URL
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
