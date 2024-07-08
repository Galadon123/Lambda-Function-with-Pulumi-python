import pulumi
import pulumi_aws as aws
import json
# Create VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Create Internet Gateways
igw = aws.ec2.InternetGateway("my-vpc-igw",
                              vpc_id=vpc.id,
                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                              tags={"Name": "my-vpc-igw"})


# Create Route Table for Publics
public_route_table = aws.ec2.RouteTable("my-vpc-public-rt",
                                        vpc_id=vpc.id,
                                        routes=[{
                                            "cidr_block": "0.0.0.0/0",
                                            "gateway_id": igw.id,
                                        }],
                                        opts=pulumi.ResourceOptions(depends_on=[igw]),
                                        tags={"Name": "my-vpc-public-rt"})

# Create Public Subnet within VPC c
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
                                                               opts=pulumi.ResourceOptions(depends_on=[public_route_table]))

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
                                                                opts=pulumi.ResourceOptions(depends_on=[private_route_table]))

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

# lambda_policy_attachment = aws.iam.RolePolicyAttachment("lambda-policy-attachment",
#     role=lambda_role.name,
#     policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
#     opts=pulumi.ResourceOptions(depends_on=[vpc]),
# )
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
# Create ECR Repository f
repository = aws.ecr.Repository("my-ecr-repo",
                                 opts=pulumi.ResourceOptions(depends_on=[lambda_role]))

# Export Outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("public_route_table_id", public_route_table.id)
pulumi.export("private_route_table_id", private_route_table.id)
pulumi.export("ec2_security_group_id", ec2_security_group.id)
pulumi.export("lambda_security_group_id", lambda_security_group.id)
pulumi.export("lambda_role_arn", lambda_role.arn)
pulumi.export("ecr_repo_url", repository.repository_url)
pulumi.export("ecr_registry", repository.registry_id)
pulumi.export("ec2_private_ip", ec2_instance.private_ip)