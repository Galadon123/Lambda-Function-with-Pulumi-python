# Automating Lambda Function Deployment with Pulumi, GitHub Actions, and Grafana Tempo for Tracing

This project demonstrates the automated deployment of a Lambda function using Pulumi and GitHub Actions, combined with an observability stack. By integrating Pulumi for infrastructure as code and GitHub Actions for continuous deployment, it ensures a smooth, repeatable process for provisioning AWS resources and deploying serverless applications. The automation setup enhances the efficiency and reliability of managing cloud infrastructure, streamlining the deployment process while maintaining high standards of observability and traceability.

![](https://github.com/Galadon123/-Lambda-Function-Deployment/blob/main/image/f.png)
### Grafana and Tracing
The observability stack, featuring Grafana, Tempo, and the OpenTelemetry Collector, is deployed on an EC2 instance. Grafana provides powerful visualization capabilities, allowing you to monitor various metrics and performance indicators. Tempo, integrated with Grafana, enables distributed tracing, helping you track the flow of requests through your system and identify performance bottlenecks. The OpenTelemetry Collector collects and exports trace data, ensuring comprehensive monitoring and insights into application behavior and performance.

![](https://github.com/Galadon123/-Lambda-Function-Deployment/blob/main/image/Screenshot%202024-07-02%20174136.png)

## Project Directory

```
project-root/
├── deploy-in-lambda/
│   ├── Dockerfile
│   ├── index.js
│   ├── package.json
│   ├── initialization/
│   │   └── initialization.js
│   └── routes/
│       ├── routes.js
│       └── tracing.js
└── infra/
|    ├── __main__.py
└── .github/
|    └── workflows/
|        ├── deploy.yml
|        └── infra.yml     
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

### Infrastructure Code Breakdown

#### `infra/__main__.py`

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

                                # Create NAT Gateway in Public Subnet
nat_gateway = aws.ec2.NatGateway("my-nat-gateway",
                                subnet_id=public_subnet.id,
                                allocation_id=igw.id,
                                opts=pulumi.ResourceOptions(depends_on=[public_subnet, igw]),
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

lambda_policy_attachment = aws.iam.RolePolicyAttachment("lambda-policy-attachment",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)
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
            }
        ]
    }""",
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)

# Attach IAM Policy to Lambda Role
lambda_policy_attachment = aws.iam.RolePolicyAttachment("lambda-policy-attachment",
    role=lambda_role.name,
    policy_arn=lambda_policy.arn,
    opts=pulumi.ResourceOptions(depends_on=[vpc]),
)
# Create ECR Repository ff
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

### We've created using Pulumi for AWS infrastructure:

1. **VPC (Virtual Private Cloud)**:
   - A virtual network in AWS with CIDR block `10.0.0.0/16`.
   - Includes an Internet Gateway (`my-vpc-igw`) for public internet access.

2. **Public Subnet**:
   - Subnet `10.0.1.0/24` in availability zone `us-east-1a`.
   - Associated with a route table (`my-vpc-public-rt`) for public internet routing.

3. **Private Subnet**:
   - Subnet `10.0.2.0/24` in availability zone `us-east-1b`.
   - Associated with a route table (`my-vpc-private-rt`) for local VPC routing.

4. **EC2 Instance**:
   - `t2.micro` instance (`my-ec2-instance`) in the public subnet.
   - Secured by a security group (`ec2-security-group`) allowing all traffic.

5. **Security Groups**:
   - **EC2 Security Group**: Allows all traffic inbound and outbound for the EC2 instance.
   - **Lambda Security Group**: Allows all traffic inbound and outbound for Lambda functions.

6. **IAM Role and Policies**:
   - **Lambda Execution Role**: Allows Lambda functions to execute with VPC access.
   - **Lambda Policy**: Grants access to read from and list objects in an S3 bucket (`lambda-function-bucket-poridhi`).

7. **ECR Repository**:
   - `my-ecr-repo` to store Docker images securely within AWS ECR.

8. **Route Tables**:
   - **Public Route Table**: Routes `0.0.0.0/0` via the Internet Gateway (`igw`) for public subnet.
  - **Private Route Table**: Routes `0.0.0.0/16` via NAT for private subnet.

9. **IAM Policy Attachments**:
   - **Lambda Execution Role Policy Attachment**: Attaches AWS managed policy for Lambda VPC access.
   - **Lambda Policy Attachment**: Attaches custom IAM policy to Lambda execution role for S3 access.

10. **Exports**:
    - Exports key resources like VPC ID, subnets IDs, security group IDs, IAM role ARN, ECR repository details, and EC2 private IP for external usage.


## Locally Set Up Node.js App

1. **Initialize Node.js Project**:
   ```sh
   cd deploy-in-lambda
   npm init -y
   ```

2. **Create `index.js`**:
```javascript
   const awsServerlessExpress = require('aws-serverless-express');
const { initializeAndFetch } = require('./initialization/initialization');
const { app, server } = require('./routes/routes');

// Initialize and fetch before handling requests
initializeAndFetch().catch((error) => {
  console.error("Initialization failed:", error);
  process.exit(1); // Exit Lambda function on initialization failure
});

exports.handler = (event, context) => {
  console.log("Handler invoked");
  return awsServerlessExpress.proxy(server, event, context, 'PROMISE').promise;
};

```
   - **Explanation**:
     - Initializes OpenTelemetry and fetches configuration data from AWS S3 before handling any incoming requests.
     - Sets up an Express server and defines a Lambda function handler to proxy HTTP requests.

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
   - **Explanation**:
     - Defines project metadata and dependencies required for the Lambda function.
     - Includes packages for AWS SDK, Express framework, and OpenTelemetry for tracing capabilities.

4. **Create `initialization.js`**:
```javascript
   const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const grpc = require('@grpc/grpc-js');
const AWS = require('aws-sdk');

const S3_BUCKET_NAME = 'lambda-function-bucket-poridhi'; // Replace with your S3 bucket name
const S3_FILE_NAME = 'pulumi-outputs.json'; // Replace with your file name

let collectorUrl = null;
let otelInitialized = false;

async function fetchCollectorUrl() {
  try {
    const s3 = new AWS.S3();
    const data = await s3.getObject({ Bucket: S3_BUCKET_NAME, Key: S3_FILE_NAME }).promise();
    const outputs = JSON.parse(data.Body.toString());
    collectorUrl = `http://${outputs.ec2_private_ip}:4317`; // Assuming the port is 4317
    console.log(`Retrieved collector URL from S3: ${collectorUrl}`);
  } catch (error) {
    console.error("Error fetching collector URL from S3:", error);
    throw error;
  }
}

async function initializeOpenTelemetry() {
  try {
    const traceExporter = new OTLPTraceExporter({
      url: collectorUrl,
      credentials: grpc.credentials.createInsecure(),
    });

    const sdk = new NodeSDK({
      traceExporter,
      instrumentations: [getNodeAutoInstrumentations()],
    });

    await sdk.start();
    otelInitialized = true;
    console.log('OpenTelemetry SDK initialized');
  } catch (error) {
    console.error("Error initializing OpenTelemetry:", error);
    throw error;
  }
}

async function initializeAndFetch() {
  try {
    await fetchCollectorUrl();
    await initializeOpenTelemetry();
  } catch (error) {
    console.error("Initialization failed:", error);
    process.exit(1); // Exit Lambda function on initialization failure
  }
}

module.exports = {
  initializeAndFetch,
};

```
   - **Explanation**:
     - **Fetches Configuration**: Retrieves configuration data (collector URL) from an AWS S3 bucket to initialize OpenTelemetry.
     - **Initializes OpenTelemetry**: Sets up the OpenTelemetry SDK with an OTLP exporter over gRPC, enabling distributed tracing.
     - **Error Handling**: Catches and logs initialization errors, ensuring proper operation of the Lambda function.

5. **Create `routes.js`**:
```javascript
   const express = require('express');
const awsServerlessExpress = require('aws-serverless-express');
const awsServerlessExpressMiddleware = require('aws-serverless-express/middleware');
const { trace, context } = require('@opentelemetry/api');
const { traceFunction } = require('./tracing');

const app = express();
const server = awsServerlessExpress.createServer(app);

app.use(express.json());
app.use(awsServerlessExpressMiddleware.eventContext());

app.get('/', async (req, res) => {
  await traceFunction('GET /', async () => {
    const activeSpan = trace.getSpan(context.active());
    if (activeSpan) {
      res.send(`Hello, World! Trace ID: ${activeSpan.spanContext().traceId}`);
    } else {
      res.send('Hello, World!'); // Fallback response if no active span
    }
  });
});

app.get('/trace', async (req, res) => {
  await traceFunction('GET /trace', async () => {
    const activeSpan = trace.getSpan(context.active());
    if (activeSpan) {
      res.send(`This route is traced with OpenTelemetry! Trace ID: ${activeSpan.spanContext().traceId}`);
    } else {
      res.send('This route is traced with OpenTelemetry!'); // Fallback response if no active span
    }
  });
});


module.exports = {
  app,
  server,
};
```
   - **Explanation**:
     - **Middleware and Server Setup**: Configures middleware for JSON parsing and AWS Lambda event handling using `aws-serverless-express`.
     - **Routes Definition**: Defines several HTTP routes (`/`, `/trace`, `/slow`, `/error`) with tracing instrumentation using OpenTelemetry API.
     - **Error Handling**: Implements error handling within routes to capture and log errors with appropriate tracing context.

6. **Create `tracing.js`**:
```javascript
  const { trace, context } = require('@opentelemetry/api');

// Middleware function to handle tracing
async function traceFunction(name, callback) {
  const currentSpan = trace.getTracer('default').startSpan(name);
  return context.with(trace.setSpan(context.active(), currentSpan), async () => {
    try {
      await callback();
    } catch (error) {
      console.error(`Error processing ${name}:`, error);
      currentSpan.setStatus({ code: 2 }); // Status code 2 represents an error
    } finally {
      currentSpan.end();
    }
  });
}

module.exports = {
  traceFunction,
};
```
   - **Explanation**:
     - **Tracing Function**: Defines a utility function (`traceFunction`) to initiate and manage spans using OpenTelemetry API.
     - **Span Management**: Starts a new span for each traced operation, ensuring proper error handling and span closure.

7. **Create `Dockerfile`**:

```dockerfile
   # Use the official AWS Lambda node image
FROM public.ecr.aws/lambda/nodejs:14

# Create directories for partitioned files
RUN mkdir -p /var/task/initialization /var/task/routes

# Copy initialization scripts
COPY initialization/ /var/task/initialization/

# Copy route definitions
COPY routes/ /var/task/routes/

# Copy Lambda function handler
COPY index.js /var/task/

# Install production dependencies (if any)
COPY package.json package-lock.json /var/task/
RUN npm install --only=production --prefix /var/task

# Set working directory
WORKDIR /var/task

# Command can be overwritten by providing a different command in the template directly.
CMD [ "index.handler" ]
```
   - **Explanation**:
     - **Base Image**: Uses the official AWS Lambda Node.js runtime image (`nodejs:16`) as the base.
     - **Code and Dependency Copy**: Copies the function code (`index.js`) and dependency manifest files (`package.json`, `package-lock.json`) into the Docker image.
     - **Dependency Installation**: Installs production dependencies using `npm install --only=production` to minimize image size and ensure runtime efficiency.
     - **Command Definition**: Specifies the command (`CMD`) to execute the Lambda function handler (`index.handler`) upon container startup.

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

    ![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/l-4.png)

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
   
## Create an IAM Role for  Access to S3 Bucket Objects

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

**Explanation**:

1. **Trigger on Push to Main Branch**: Executes the workflow when code is pushed to the main branch within the `infra` directory.
2. **Checkout Code**: Uses the `actions/checkout@v3` to pull the latest code from the repository.
3. **Set up Python Environment**: Installs Python and sets up a virtual environment with required dependencies like `pulumi` and `pulumi-aws`.
4. **Configure AWS Credentials**: Sets up AWS credentials using GitHub secrets to interact with AWS services.
5. **Run Pulumi Commands**: Logs into Pulumi, selects the appropriate stack, refreshes the state, and applies the changes using Pulumi.
6. **Export Pulumi Outputs to S3**: Exports the Pulumi stack outputs to a JSON file and uploads it to an S3 bucket for use in other workflows.
7. **Clean Up**: Deletes the local copy of the Pulumi outputs JSON file after uploading to S3.


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
**Explanation**:

1. **Trigger on Push to Main Branch**: Executes the workflow when code is pushed to the main branch within the `deploy-in-lambda` directory.
2. **Trigger on Pulumi Workflow Completion**: Runs this workflow after the "Pulumi Deploy" workflow completes successfully.
3. **Checkout Code**: Uses the `actions/checkout@v3` to pull the latest code from the repository.
4. **Ensure AWS Credentials**: Configures AWS credentials using GitHub secrets to interact with AWS services.
5. **Download Pulumi Outputs**: Retrieves Pulumi output variables from an S3 bucket and saves them locally.
6. **Parse Pulumi Outputs**: Extracts essential variables like ECR repository URL, registry ID, Lambda role ARN, private subnet ID, and security group ID from the Pulumi outputs.
7. **Install AWS CLI**: Installs the AWS Command Line Interface to facilitate AWS operations.
8. **Login to AWS ECR**: Authenticates Docker to AWS ECR using AWS CLI for image push.
9. **Build and Push Docker Image**: Builds the Docker image from the `deploy-in-lambda` directory and pushes it to AWS ECR using Docker.
10. **Create or Update Lambda Function**: Creates a new Lambda function or updates an existing one using the newly pushed Docker image, configuring it with the appropriate VPC, subnet, and security group settings.

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

## Testing Lambda Function with JSON Query


1. **Select Your Lambda Function**:
   - In the Lambda console, find and select your deployed Lambda function.

2. **Create a Test Event**:
   - Click on the "Test" button in the top-right corner.
   - If this is your first time, you will be prompted to configure a test event.

3. **Configure the Test Event**:
   - Enter a name for the test event.
   - Replace the default JSON with your desired test JSON query, for example:
     ```json
     {
       "httpMethod": "GET",
       "path": "/",
       "headers": {
         "Content-Type": "application/json"
       },
       "body": null,
       "isBase64Encoded": false
     }
     ```

4. **Save and Test**:
   - Save the test event configuration.
   - Click on "Test" to execute the test event.

5. **View Results**:
   - Check the execution results, which will appear on the Lambda console.
   - Review the logs and output to verify that the Lambda function executed correctly.

   ![](https://github.com/Galadon123/Lambda-Function-with-Pulumi-python/blob/main/image/ajke-2.png)

This process allows you to test your Lambda function directly within the AWS Lambda console using a JSON query.

## EC2 Instance Setup for Grafana, Tempo, and OpenTelemetry Collector

### Step 1: Install Docker
1. Update packages and install Docker:
    ```sh
    sudo apt-get update -y
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
    ```

### Step 2: Install Docker Compose
1. Install Docker Compose:
    ```sh
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```

### Step 3: Set Up Directory Structure
1. Create a directory for your setup:
    ```sh
    mkdir ~/grafana-tempo-otel
    cd ~/grafana-tempo-otel
    ```

### Step 4: Create Configuration Files

#### `tempo.yaml`
Create `tempo.yaml` with the following content:
```yaml
auth_enabled: false

server:
  http_listen_port: 3200

ingester:
  trace_idle_period: 30s
  max_block_bytes: 5000000
  max_block_duration: 5m

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces

compactor:
  compaction:
    block_retention: 48h

querier:
  frontend_worker:
    frontend_address: 127.0.0.1:9095
```

#### `otel-collector-config.yaml`
Create `otel-collector-config.yaml` with the following content:
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"

processors:
  batch:

exporters:
  otlp:
    endpoint: "tempo:4317"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp]
```

#### `docker-compose.yml`
Create `docker-compose.yml` with the following content:
```yaml
version: '3'

services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  tempo:
    image: grafana/tempo:latest
    ports:
      - "3200:3200"
    command: ["tempo", "serve", "--config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml

  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"  # Expose the OTLP gRPC endpoint
      - "4318:4318"  # Expose the OTLP HTTP endpoint
```

### Step 5: Start Services
1. Navigate to the directory where you created the files and start the services using Docker Compose:
    ```sh
    cd ~/grafana-tempo-otel
    sudo docker-compose up -d
    ```

## Example Scenario: Trace Data Flow

1. **Application (Lambda Function)**:
    - Your application generates trace data and sends it to the OpenTelemetry Collector endpoint (`http://${ec2InstancePrivateIP}:4317`).

2. **OpenTelemetry Collector**:
    - The Collector receives the traces via the OTLP receiver.
    - The traces pass through the processing pipeline.
    - The `logging` exporter logs the trace data for debugging.
    - The `otlp` exporter sends the trace data to Tempo.

3. **Grafana Tempo**:
    - Tempo receives the trace data on its gRPC endpoint (`tempo:4317`).
    - Tempo processes and stores the traces in `/tmp/tempo/traces`.

4. **Grafana**:
    - Grafana queries Tempo to retrieve the stored trace data.
    - The traces are visualized in Grafana’s user interface, allowing you to analyze them.

## Grafana Setup for Traces with Tempo

### Step 1: Access Grafana
1. Open a web browser and navigate to `http://<ec2_instance_public_ip>:3000`.
2. Log in with the default credentials:
    - **Username**: admin
    - **Password**: admin

### Step 2: Add Tempo Data Source
1. In the Grafana UI, go to **Configuration** (gear icon) > **Data Sources**.
2. Click on **Add data source**.
3. Select **Tempo** from the list of available data sources.

### Step 3: Configure Tempo Data Source
1. Set the **HTTP URL** to `http://tempo:3200`.
2. Click **Save & Test** to ensure the connection to Tempo is successful.

### Step 4: Create a Dashboard
1. Go to **Create** (plus icon) > **Dashboard**.
2. Click on **Add new panel**.

### Step 5: Query Traces
1. In the query editor, select the Tempo data source.
2. Use TraceQL to query the traces. For example:
    ```traceql
    {}
    ```
    ![TraceQL](https://github.com/Galadon123/-Lambda-Function-Deployment/blob/main/image/o-1.png)
## Step 6: Managing and Understanding Trace Data
![](https://github.com/Galadon123/-Lambda-Function-Deployment/blob/main/image/o-2.png)

#### Explanation of Image Observations

1. **Disconnected Dots in Grafana Dashboard**: The dots represent trace data points. Disconnected dots indicate that traces are not being generated continuously.
2. **Lambda Function Invocation**: Each dot corresponds to a single invocation of the Lambda function. The intervals between dots show the time gap between successive invocations.


## Summary

This documentation provides a detailed guide on setting up an automated workflow to deploy a Node.js Lambda function using Pulumi and GitHub Actions. By organizing infrastructure code in Pulumi and leveraging GitHub Actions for CI/CD, we ensure a smooth and repeatable deployment process.

