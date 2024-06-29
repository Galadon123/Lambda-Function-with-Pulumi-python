import pulumi
import pulumi_aws as aws

class VPC:
    def __init__(self, name: str, cidr_block: str):
        self.vpc = aws.ec2.Vpc(name,
                               cidr_block=cidr_block,
                               tags={"Name": name})
        pulumi.export("vpc_id", self.vpc.id)


class Subnet:
    def __init__(self, name: str, vpc_id: pulumi.Output[str], cidr_block: str, availability_zone: str):
        self.subnet = aws.ec2.Subnet(name,
                                     vpc_id=vpc_id,
                                     cidr_block=cidr_block,
                                     availability_zone=availability_zone,
                                     tags={"Name": name})
        pulumi.export("private_subnet_id", self.subnet.id)


class ECRRepository:
    def __init__(self, name: str):
        self.repository = aws.ecr.Repository(name,
                                             image_scanning_configuration={"scanOnPush": True},
                                             tags={"Name": name})
        pulumi.export("ecr_repo_url", self.repository.repository_url)
        pulumi.export("ecr_registry", self.repository.registry_id)


class LambdaRole:
    def __init__(self, name: str):
        self.role = aws.iam.Role(name,
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
        self.policy = aws.iam.RolePolicy(f"{name}-policy",
                                         role=self.role.id,
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
        pulumi.export("lambda_role_arn", self.role.arn)


class SecurityGroup:
    def __init__(self, name: str, vpc_id: pulumi.Output[str]):
        self.security_group = aws.ec2.SecurityGroup(name,
                                                    vpc_id=vpc_id,
                                                    egress=[{
                                                        "protocol": "-1",
                                                        "from_port": 0,
                                                        "to_port": 0,
                                                        "cidr_blocks": ["0.0.0.0/0"],
                                                    }],
                                                    tags={"Name": name})
        pulumi.export("lambda_security_group_id", self.security_group.id)


# Create the resources using the classes
vpc = VPC("my-vpc", "10.0.0.0/16")
private_subnet = Subnet("private-subnet", vpc.vpc.id, "10.0.1.0/24", "us-east-1a")
ecr_repo = ECRRepository("my-lambda-function")
lambda_role = LambdaRole("lambda-role")
lambda_security_group = SecurityGroup("lambda-security-group", vpc.vpc.id)
