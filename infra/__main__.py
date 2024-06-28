import pulumi
import pulumi_aws as aws

# Create a VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Create a private subnet within the VPC
private_subnet = aws.ec2.Subnet("private-subnet",
                                vpc_id=vpc.id,
                                cidr_block="10.0.1.0/24",
                                availability_zone="us-east-1a",
                                tags={"Name": "private-subnet"})

# Create an ECR repository for Lambda functions
ecr_repo = aws.ecr.Repository("my-ecr-repo",
                              image_tag_mutability="MUTABLE",
                              image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                                  scan_on_push=True),
                              tags={"Name": "my-ecr-repo"})

# Create an IAM role for Lambda with an assume role policy allowing Lambda service
lambda_role = aws.iam.Role("lambda-role",
                           assume_role_policy=aws.iam.get_policy_document(statements=[aws.iam.GetPolicyDocumentStatementArgs(
                               actions=["sts:AssumeRole"],
                               principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                                   type="Service",
                                   identifiers=["lambda.amazonaws.com"]
                               )],
                               effect="Allow",
                           )]).json)

# Attach policies to the Lambda role for necessary actions
lambda_policy = aws.iam.RolePolicy("lambda-policy",
                                   role=lambda_role.id,
                                   policy=aws.iam.get_policy_document(statements=[
                                       aws.iam.GetPolicyDocumentStatementArgs(
                                           actions=[
                                               "logs:CreateLogGroup",
                                               "logs:CreateLogStream",
                                               "logs:PutLogEvents",
                                               "ecr:GetDownloadUrlForLayer",
                                               "ecr:BatchGetImage",
                                               "ecr:BatchCheckLayerAvailability",
                                               "ec2:CreateNetworkInterface",
                                               "ec2:DescribeNetworkInterfaces",
                                               "ec2:DeleteNetworkInterface"
                                           ],
                                           resources=["*"],
                                           effect="Allow",
                                       )
                                   ]).json,
                                   opts=pulumi.ResourceOptions(depends_on=[lambda_role]))

# Create a security group for the Lambda function in the VPC
lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                              vpc_id=vpc.id,
                                              egress=[aws.ec2.SecurityGroupEgressArgs(
                                                  protocol="-1",
                                                  from_port=0,
                                                  to_port=0,
                                                  cidr_blocks=["0.0.0.0/0"],
                                              )],
                                              tags={"Name": "lambda-security-group"})

# Export the created resources' identifiers for easy access and reference
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("ecr_registry_id", ecr_repo.registry_id)
pulumi.export("lambda_role_arn", lambda_role.arn)
pulumi.export("lambda_security_group_id", lambda_security_group.id)
