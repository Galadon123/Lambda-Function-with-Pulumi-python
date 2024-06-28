import pulumi
import pulumi_aws as aws

# Define a method to handle the creation of resources and ensure they are created sequentially
def main():
    # Create a VPC
    vpc = aws.ec2.Vpc("my-vpc",
                      cidr_block="10.0.0.0/16",
                      tags={"Name": "my-vpc"})

    # Create a private subnet within the VPC
    private_subnet = aws.ec2.Subnet("private-subnet",
                                    vpc_id=vpc.id,
                                    cidr_block="10.0.1.0/24",
                                    availability_zone="us-east-1a",
                                    tags={"Name": "private-subnet"},
                                    opts=pulumi.ResourceOptions(depends_on=[vpc]))

    # Create an ECR repository
    ecr_repo = aws.ecr.Repository("my-ecr-repo",
                                  image_tag_mutability="MUTABLE",
                                  image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                                      scan_on_push=True),
                                  tags={"Name": "my-ecr-repo"},
                                  opts=pulumi.ResourceOptions(depends_on=[vpc]))

    # Define the IAM role's assume role policy JSON
    assume_role_policy = aws.iam.get_policy_document(statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            actions=["sts:AssumeRole"],
            principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                type="Service",
                identifiers=["lambda.amazonaws.com"]
            )],
            effect="Allow",
        )
    ]).json

    # Create an IAM role for Lambda
    lambda_role = aws.iam.Role("lambda-role",
                               assume_role_policy=assume_role_policy,
                               opts=pulumi.ResourceOptions(depends_on=[vpc]))

    # Attach a policy to the Lambda role that allows necessary actions
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

    # Create a security group for Lambda within the VPC
    lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                                  vpc_id=vpc.id,
                                                  egress=[aws.ec2.SecurityGroupEgressArgs(
                                                      protocol="-1",
                                                      from_port=0,
                                                      to_port=0,
                                                      cidr_blocks=["0.0.0.0/0"],
                                                  )],
                                                  tags={"Name": "lambda-security-group"},
                                                  opts=pulumi.ResourceOptions(depends_on=[vpc]))

    # Export the VPC ID, Subnet ID, Security Group ID, ECR Repository URL, and Lambda Role ARN
    pulumi.export("vpc_id", vpc.id)
    pulumi.export("private_subnet_id", private_subnet.id)
    pulumi.export("ecr_repo_url", ecr_repo.repository_url)
    pulumi.export("ecr_registry_id", ecr_repo.registry_id)
    pulumi.export("lambda_role_arn", lambda_role.arn)
    pulumi.export("lambda_security_group_id", lambda_security_group.id)

if __name__ == "__main__":
    main()
