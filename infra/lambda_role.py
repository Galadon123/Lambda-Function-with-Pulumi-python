import pulumi
import pulumi_aws as aws

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
