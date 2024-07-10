

# import pulumi
# import pulumi_aws as aws

# def create_ec2_instance(public_subnet_id, ec2_security_group_id):
#     ec2_instance = aws.ec2.Instance("my-ec2-instance",
#         instance_type="t2.micro",
#         vpc_security_group_ids=[ec2_security_group_id],
#         subnet_id=public_subnet_id,
#         ami="ami-04a81a99f5ec58529",  # Example AMI ID, replace with your desired AMI
#         tags={"Name": "my-ec2-instance"}
#     )
#     return ec2_instance