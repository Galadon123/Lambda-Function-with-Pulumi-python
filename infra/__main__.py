from vpc import VPC
from subnet import Subnet
from ecr_repository import ECRRepository
from lambda_role import LambdaRole
from security_group import SecurityGroup

# Create the resources using the classes
vpc = VPC("my-vpc", "10.0.0.0/16")
private_subnet = Subnet("private-subnet", vpc.vpc.id, "10.0.1.0/24", "us-east-1a")
ecr_repo = ECRRepository("my-lambda-function")
lambda_role = LambdaRole("lambda-role")
lambda_security_group = SecurityGroup("lambda-security-group", vpc.vpc.id)
