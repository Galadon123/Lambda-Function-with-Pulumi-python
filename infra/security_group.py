import pulumi
import pulumi_aws as aws

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
