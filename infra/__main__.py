import pulumi
import pulumi_aws as aws
import json

# Create an IAM role for Lambda
assume_role_policy = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Action": "sts:AssumeRole",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
    }]
})

lambda_role = aws.iam.Role("lambda-role-test",
                           assume_role_policy=assume_role_policy)

# Attach a simple policy to the Lambda role
simple_policy_document = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": "logs:*",
        "Resource": "*"
    }]
})

lambda_policy = aws.iam.RolePolicy("lambda-policy-test",
                                   role=lambda_role.id,
                                   policy=simple_policy_document)

# Export the role ARN to verify creation
pulumi.export("lambda_role_arn", lambda_role.arn)
