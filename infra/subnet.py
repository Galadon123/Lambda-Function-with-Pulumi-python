import pulumi
import pulumi_aws as aws

class Subnet:
    def __init__(self, name: str, vpc_id: pulumi.Output[str], cidr_block: str, availability_zone: str):
        self.subnet = aws.ec2.Subnet(name,
                                     vpc_id=vpc_id,
                                     cidr_block=cidr_block,
                                     availability_zone=availability_zone,
                                     tags={"Name": name})
        pulumi.export("private_subnet_id", self.subnet.id)
