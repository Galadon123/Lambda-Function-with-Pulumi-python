# Automating Lambda Function Deployment with Pulumi and GitHub Actions

This project demonstrates how to automate the deployment of a Lambda function using Pulumi and GitHub Actions. We will set up infrastructure with Pulumi, deploy a Node.js Lambda function, and automate the entire process using GitHub Actions.

![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/Screenshot%202024-07-01%20210422.png)

## Project Directory

```
project-root/
├── infra/
│   ├── __init__.py
│   ├── __main__.py
│   ├── vpc.py
│   ├── subnet.py
│   ├── ecr_repository.py
│   ├── lambda_role.py
│   └── security_group.py
├── deploy-in-lambda/
│   ├── index.js
│   ├── package.json
│   └── Dockerfile
├── .github/
│   └── workflows/
│       ├── infra.yml
│       └── deploy.yml       
```

### Locally Set Up Pulumi for the `infra` Directory

#### Step 1: Install Pulumi

```sh
curl -fsSL https://get.pulumi.com | sh
```

This command installs Pulumi on your local machine.

#### Step 2: Log in to Pulumi

```sh
pulumi login
```

This command logs you into your Pulumi account, enabling you to manage your infrastructure as code.

#### Step 3: Initialize Pulumi Project

```sh
cd infra
pulumi new aws-python
```

This command initializes a new Pulumi project using the AWS Python template in the `infra` directory.

#### Step 4: Configure AWS Credentials

Ensure that your AWS credentials are set up in your environment:

```sh
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

This step ensures that Pulumi can authenticate with AWS to create and manage resources.

#### Step 5: Install Python Dependencies

```sh
python -m venv venv
source venv/bin/activate
pip install pulumi pulumi-aws
```

These commands create a virtual environment, activate it, and install the necessary Pulumi packages.

### Infrastructure Code Breakdown

#### `infra/__main__.py`

This is the main entry point for Pulumi to execute. It imports and initializes the infrastructure components.

```python
import pulumi
import pulumi_aws as aws
import json
# Create VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Create Internet Gateway
igw = aws.ec2.InternetGateway("my-vpc-igw",
                              vpc_id=vpc.id,
                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                              tags={"Name": "my-vpc-igw"})

# Create Route Table for Public Subnet
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

# Create Route Table for Private Subnet
private_route_table = aws.ec2.RouteTable("my-vpc-private-rt",
                                         vpc_id=vpc.id,
                                         routes=[{
                                             "cidr_block": "10.0.0.0/16",
                                             "gateway_id": "local",
                                         }],
                                         opts=pulumi.ResourceOptions(depends_on=[igw]),
                                         tags={"Name": "my-vpc-private-rt"})

# Associate Route Table with Private Subnet
private_route_table_association = aws.ec2.RouteTableAssociation("private-subnet-association",
                                                                subnet_id=private_subnet.id,
                                                                route_table_id=private_route_table.id,
                                                                opts=pulumi.ResourceOptions(depends_on=[private_route_table]))

# Create Security Group for Lambda functions
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


# Create ECR Repository f
repository = aws.ecr.Repository("my-ecr-repo",
                                 opts=pulumi.ResourceOptions(depends_on=[lambda_role]))

# Export Outputas
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
```

**Explanation**: This class initializes a new security group within the specified VPC with unrestricted outbound access, and exports its ID.

## Locally Set Up Node.js App

1. **Initialize Node.js Project**:
    ```sh
    cd deploy-in-lambda
    npm init -y
    ```

2. **Create `index.js`**:
    ```javascript
    // deploy-in-lambda/index.js
    exports.handler = async (event) => {
        const response = {
            statusCode: 200,
            body: JSON.stringify('Hello World!'),
        };
        return response;
    };
    ```

3. **Create `package.json`**:
```json
{
  "name": "lambda-function",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "dependencies": {
    "@grpc/grpc-js": "^1.8.12",
    "@opentelemetry/api": "^1.9.0",
    "@opentelemetry/auto-instrumentations-node": "^0.47.1",
    "@opentelemetry/exporter-otlp-grpc": "^0.26.0",
    "@opentelemetry/sdk-node": "^0.52.1",
    "aws-sdk": "^2.1000.0",
    "aws-serverless-express": "^3.4.0",
    "express": "^4.19.2"
  },
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "author": "",
  "license": "ISC"
}
```

4. **Install Dependencies**:
    ```sh
    npm install
    ```

## Dockerfile

```dockerfile
# Use the official AWS Lambda node image
FROM public.ecr.aws/lambda/nodejs:16

# Copy function code
COPY index.js package.json package-lock.json ./

# Install production dependencies
RUN npm install --only=production

# Command can be overwritten by providing a different command in the template directly.
CMD [ "index.handler" ]
```

## Create a Token for Login to Pulumi

1. **Create Pulumi Access Token**:
    - Go to the Pulumi Console at https://app.pulumi.com.
    - Navigate to `Settings` > `Access Tokens`.
    - Click `Create Token`, give it a name, and copy the token.

    ![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-2.png)

## Create a GitHub Repo and Set Up Secrets

1. **Create a GitHub Repository**:
    - Navigate to GitHub and create a new repository.

2. **Add GitHub Secrets**:
    - Go to `Settings` > `Secrets and variables` > `Actions`.
    - Add the following secrets:
        - `AWS_ACCESS_KEY_ID`: Your AWS access key ID.
        - `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
        - `PULUMI_ACCESS_TOKEN`: Your Pulumi access token.

    ![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-3.png)

## Create S3 Bucket and Set Up Policies

1. **Create S3 Bucket**:
    - Go to the AWS Management Console.
    - Navigate to S3 and create a new bucket. Name it `lambda-function-bucket-poridhi`.
    - Follow the visual representation 

    ### Detailed Steps for Creating an IAM Role to Allow Public Access to S3 Bucket Objects

#### Step 1: Create an S3 Bucket

1. **Navigate to S3 Service**
   - Go to the AWS Management Console.
   - Navigate to the S3 service.

2. **Create a New Bucket**
   - Click on the "Create bucket" button.
   
   ![Create Bucket](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-4.png)

3. **Configure the Bucket**
   - Enter the bucket name (e.g., `lambda-function-bucket-poridhi`).
   - Select the appropriate region (e.g., `US East (N. Virginia) us-east-1`).
   - Choose "General purpose" as the bucket type.
   
   ![Configure Bucket](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-5.png)

5. **Enable Bucket Versioning**
   - Enable bucket versioning for better data management.
   
   ![Bucket Versioning](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-7.png)

6. **Create the Bucket**
   - Click on "Create bucket" to finalize the creation.
   
Sure, here are the detailed steps for creating an IAM role that allows public access to objects in the `lambda-function-bucket-poridhi` bucket:

## Create an IAM Role for Public Access to S3 Bucket Objects

1. **Navigate to the IAM Roles Section**
   - Go to the AWS Management Console.
   - Navigate to the IAM service.
   - Select "Roles" from the left-hand menu.
   - Click on the "Create role" button.

   ![Create Role](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-9.png)

2. **Select Trusted Entity Type**
   - Choose "AWS service" as the trusted entity type.
   - In the "Use case" dropdown, select "Lambda".
   - Click "Next: Permissions".

   ![Select Trusted Entity](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-10.png)

3. **Attach Inline Policy**
   - In the "Permissions" section, click on the "Create inline policy" button.

   ![Create Inline Policy](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-11.png)

4. **Specify Permissions using JSON**
   - Switch to the "JSON" tab.
   - Add the following JSON policy to allow public read access to objects in the specified S3 bucket:
```json
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::lambda-function-bucket-poridhi/pulumi-outputs.json"
        }
     ]
    }
```
   - Click "Review policy".

   ![Specify Permissions](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-12.png)

5. **Review and Create Policy**
   - Give the policy a name (e.g., `PublicAccessToLambdaBucket`).
   - Review the policy details.
   - Click "Create policy".

6. **Attach the Policy to the Role**
   - Ensure that the newly created inline policy is attached to the role.
   - Proceed with the role creation by clicking "Next: Tags".


8. **Review and Create Role**
   - Review the role details.
   - Give the role a name (e.g., `LambdaS3PublicAccessRole`).
   - Click "Create role".

## Create Two Workflows

### `infra.yml`

```yaml
name: Pulumi Deploy

on:
  push:
    branches:
      - main
    paths:
      - 'infra/**'

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install pulumi pulumi-aws

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Pulumi login
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
        run: |
          source venv/bin/activate
          pulumi login

      - name: Pulumi stack select
        run: |
          source venv/bin/activate
          pulumi stack select dev-project-lambda --cwd infra

      - name: Pulumi refresh
        run: |
          source venv/bin/activate
          pulumi refresh --yes --cwd infra

      - name: Pulumi up
        run: |
          source venv/bin/activate
          pulumi up --yes --cwd infra

      - name: Export Pulumi outputs to S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
          S3_BUCKET_NAME: lambda-function-bucket-poridhi
          S3_FILE_NAME: pulumi-outputs.json
        run: |
          source venv/bin/activate
          pulumi stack output --json --cwd infra > outputs.json
          aws s3 cp outputs.json s3://$S3_BUCKET_NAME/$S3_FILE_NAME

      - name: Clean up outputs.json
        run: rm outputs.json
```

### `deploy-lambda.yml`

```yaml
name: Deploy Lambda Function

on:
  push:
    branches:
      - main
    paths:
      - 'deploy-in-lambda/**'

  workflow_run:
    workflows: ["Pulumi Deploy"]
    types:
      - completed

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      # Ensure AWS credentials are configured
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      # Download Pulumi outputs from S3 bucket
      - name: Download Pulumi outputs from S3
        run: |
          aws s3 cp s3://lambda-function-bucket-poridhi/pulumi-outputs.json ./outputs.json

      # Parse Pulumi outputs and set environment variables
      - name: Parse Pulumi outputs
        id: parse_outputs
        run: |
          cat ./outputs.json
          ECR_REPO_URL=$(jq -r '.ecr_repo_url' ./outputs.json)
          ECR_REGISTRY=$(jq -r '.ecr_registry' ./outputs.json)
          LAMBDA_ROLE_ARN=$(jq -r '.lambda_role_arn' ./outputs.json)
          PRIVATE_SUBNET_ID=$(jq -r '.private_subnet_id' ./outputs.json)
          SECURITY_GROUP_ID=$(jq -r '.lambda_security_group_id' ./outputs.json)
          echo "ECR_REPO_URL=$ECR_REPO_URL" >> $GITHUB_ENV
          echo "ECR_REGISTRY=$ECR_REGISTRY" >> $GITHUB_ENV
          echo "PRIVATE_SUBNET_ID=$PRIVATE_SUBNET_ID" >> $GITHUB_ENV
          echo "SECURITY_GROUP_ID=$SECURITY_GROUP_ID" >> $GITHUB_ENV
          echo "LAMBDA_ROLE_ARN=$LAMBDA_ROLE_ARN" >> $GITHUB_ENV

      # Install AWS CLI
      - name: Install AWS CLI
        run: |
          sudo apt-get update
          sudo apt-get install -y python3-pip
          pip3 install awscli

      # Login to AWS ECR
      - name: Login to AWS ECR
        env:
          AWS_REGION: us-east-1
          ECR_REPO_URL: ${{ env.ECR_REPO_URL }}
        run: |
          aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL

      # Build and push Docker image
      - name: Build and push Docker image
        env:
          ECR_REPO_URL: ${{ env.ECR_REPO_URL }}
          IMAGE_TAG: latest
        run: |
          cd deploy-in-lambda
          docker build -t $ECR_REPO_URL:$IMAGE_TAG .
          docker push $ECR_REPO_URL:$IMAGE_TAG

      # Create or update Lambda function
      - name: Create or update Lambda function
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
          ECR_REPO_URL: ${{ env.ECR_REPO_URL }}
          IMAGE_TAG: latest
          LAMBDA_ROLE_ARN: ${{ env.LAMBDA_ROLE_ARN }}
        run: |
          FUNCTION_NAME=my-lambda-function
          IMAGE_URI=$ECR_REPO_URL:$IMAGE_TAG
          EXISTING_FUNCTION=$(aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION 2>&1 || true)
          if echo "$EXISTING_FUNCTION" | grep -q 'ResourceNotFoundException'; then
            echo "Creating new Lambda function..."
            aws lambda create-function \
              --function-name $FUNCTION_NAME \
              --package-type Image \
              --code ImageUri=$IMAGE_URI \
              --role $LAMBDA_ROLE_ARN \
              --vpc-config SubnetIds=$PRIVATE_SUBNET_ID,SecurityGroupIds=$SECURITY_GROUP_ID \
              --region $AWS_REGION
          else
            echo "Updating existing Lambda function..."
            aws lambda update-function-code \
              --function-name $FUNCTION_NAME \
              --image-uri $IMAGE_URI \
              --region $AWS_REGION
          fi
```

## Git Push the Project

1. **Initialize Git Repository**:
    ```sh
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    ```

2. **Add Remote and Push**:
    ```sh
    git remote add origin https://github.com/yourusername/your-repo.git
    git push -u origin main
    ```

## Observe the Workflow Actions Section for Errors

- Navigate to the `Actions` tab in your GitHub repository.
- Observe the workflows and ensure they run without errors.
- If errors occur, click on the failed job to view the logs and debug accordingly.

![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-w-1.png)
![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-w-2.png)

## Create an API Gateway (HTTP) with AWS Lambda Function

1. **Create API Gateway**:
    - Go to the AWS Management Console.
    - Navigate to API Gateway and create a new HTTP API.

2. **Integrate with Lambda**:
    - Create a new integration with the Lambda function deployed by your GitHub Actions workflow.
    - Deploy the API and note the invoke URL.

## Test Using the API

- Use the API Gateway's invoke URL to test your Lambda function.

![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-13.png)
- For example, if your API Gateway's invoke URL is `https://api-id.execute-api.us-east-1.amazonaws.com`, you can test it using curl or Postman:
    ```sh
    curl https://api-id.execute-api.us-east-1.amazonaws.com
    ```
![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-1.png)
By following these steps, you can automate the deployment of a Lambda function, ensuring a consistent and efficient workflow from code changes to deployment.
## Summary

This documentation provides a detailed guide on setting up an automated workflow to deploy a Node.js Lambda function using Pulumi and GitHub Actions. By organizing infrastructure code in Pulumi and leveraging GitHub Actions for CI/CD, we ensure a smooth and repeatable deployment process.

