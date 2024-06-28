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
ecr_repo = aws.ecr.Repository("my-lambda-function",
                              image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                                  scan_on_push=True),
                              tags={"Name": "my-lambda-function"})

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

# Define IAM policy document
policy_document = aws.iam.get_policy_document(statements=[
    aws.iam.GetPolicyDocumentStatementArgs(
        effect="Allow",
        actions=[
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
        ],
        resources=["arn:aws:logs:*:*:*"]
    ),
    aws.iam.GetPolicyDocumentStatementArgs(
        effect="Allow",
        actions=[
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability"
        ],
        resources=["*"]
    ),
    aws.iam.GetPolicyDocumentStatementArgs(
        effect="Allow",
        actions=[
            "ec2:CreateNetworkInterface",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DeleteNetworkInterface"
        ],
        resources=["*"]
    )
])

lambda_policy = aws.iam.RolePolicy("lambda-policy",
                                   role=lambda_role.id,
                                   policy=policy_document.json,
                                   opts=pulumi.ResourceOptions(depends_on=[lambda_role]))

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

# Export the VPC ID, Subnet ID, and ECR Repository URL
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
