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

# IAM role for Lambda with policy to access ECR
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

# Custom policy for managing ECR
ecr_policy_document = aws.iam.get_policy_document(statements=[
    aws.iam.GetPolicyDocumentStatementArgs(
        effect="Allow",
        actions=[
            "ecr:DeleteRepository",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability",
            "ecr:PutImage",
            "ecr:InitiateLayerUpload",
            "ecr:UploadLayerPart",
            "ecr:CompleteLayerUpload",
            "ecr:DescribeRepositories",
            "ecr:ListImages",
            "ecr:DeleteRepositoryPolicy",
            "ecr:SetRepositoryPolicy"
        ],
        resources=[ecr_repo.arn]
    )
])

# Attach the custom ECR policy to the Lambda role
lambda_ecr_policy = aws.iam.RolePolicy("lambda-ecr-policy",
                                      role=lambda_role.id,
                                      policy=ecr_policy_document.json)

# Create a security group for Lambda in the VPC
lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                              vpc_id=vpc.id,
                                              egress=[aws.ec2.SecurityGroupEgressArgs(
                                                  protocol="-1",
                                                  from_port=0,
                                                  to_port=0,
                                                  cidr_blocks=["0.0.0.0/0"],
                                              )],
                                              tags={"Name": "lambda-security-group"})

# Export the IDs and URLs for easy access
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("ecr_repo_arn", ecr_repo.arn)
pulumi.export("lambda_role_arn", lambda_role.arn)
