import pulumi
import pulumi_aws as aws

class VPC:
    def __init__(self, name: str, cidr_block: str):
        self.vpc = aws.ec2.Vpc(name,
                               cidr_block=cidr_block,
                               tags={"Name": name})
        pulumi.export("vpc_id", self.vpc.id)
