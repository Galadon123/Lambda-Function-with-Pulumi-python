import pulumi
import pulumi_aws as aws

class Vpc:
    def __init__(self, name: str, cidr_block: str, tags: dict):
        self.vpc = aws.ec2.Vpc(name,
                               cidr_block=cidr_block,
                               tags=tags)

    @property
    def id(self):
        return self.vpc.id

class Subnet:
    def __init__(self, name: str, vpc_id: pulumi.Output[str], cidr_block: str, availability_zone: str, tags: dict):
        self.subnet = aws.ec2.Subnet(name,
                                     vpc_id=vpc_id,
                                     cidr_block=cidr_block,
                                     availability_zone=availability_zone,
                                     tags=tags)

    @property
    def id(self):
        return self.subnet.id

class EcrRepository:
    def __init__(self, name: str, image_scanning_configuration: dict, tags: dict):
        self.repository = aws.ecr.Repository(name,
                                             image_scanning_configuration=image_scanning_configuration,
                                             tags=tags)

    @property
    def repository_url(self):
        return self.repository.repository_url

class IamRole:
    def __init__(self, name: str, assume_role_policy: str):
        self.role = aws.iam.Role(name,
                                 assume_role_policy=assume_role_policy)

    @property
    def id(self):
        return self.role.id

class IamRolePolicy:
    def __init__(self, name: str, role_id: pulumi.Output[str], policy: str):
        self.policy = aws.iam.RolePolicy(name,
                                         role=role_id,
                                         policy=policy)

class SecurityGroup:
    def __init__(self, name: str, vpc_id: pulumi.Output[str], egress: list, tags: dict):
        self.security_group = aws.ec2.SecurityGroup(name,
                                                    vpc_id=vpc_id,
                                                    egress=egress,
                                                    tags=tags)

    @property
    def id(self):
        return self.security_group.id

# Create resources
vpc = Vpc("my-vpc", "10.0.0.0/16", {"Name": "my-vpc"})
private_subnet = Subnet("private-subnet", vpc.id, "10.0.1.0/24", "us-east-1a", {"Name": "private-subnet"})
ecr_repo = EcrRepository("my-lambda-function", {"scanOnPush": True}, {"Name": "my-lambda-function"})
lambda_role = IamRole("lambda-role", """{
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
lambda_policy = IamRolePolicy("lambda-policy", lambda_role.id, """{
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
lambda_security_group = SecurityGroup("lambda-security-group", vpc.id, [{
    "protocol": "-1",
    "from_port": 0,
    "to_port": 0,
    "cidr_blocks": ["0.0.0.0/0"],
}], {"Name": "lambda-security-group"})

# Export the IDs
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("lambda_security_group_id", lambda_security_group.id)
