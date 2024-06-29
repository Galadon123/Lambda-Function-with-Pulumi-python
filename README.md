# Automating Lambda Function Deployment with Pulumi and GitHub Actions

This project demonstrates how to automate the deployment of a Lambda function using Pulumi and GitHub Actions. We will set up infrastructure with Pulumi, deploy a Node.js Lambda function, and automate the entire process using GitHub Actions.

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

## Locally Set Up Pulumi for the `infra` Directory

1. **Install Pulumi**:
    ```sh
    curl -fsSL https://get.pulumi.com | sh
    ```

2. **Log in to Pulumi**:
    ```sh
    pulumi login
    ```

3. **Initialize Pulumi Project**:
    ```sh
    cd infra
    pulumi new aws-python
    ```

4. **Configure AWS Credentials**:
    Ensure that your AWS credentials are set up in your environment:
    ```sh
    export AWS_ACCESS_KEY_ID=your_access_key_id
    export AWS_SECRET_ACCESS_KEY=your_secret_access_key
    ```

5. **Install Python Dependencies**:
    ```sh
    python -m venv venv
    source venv/bin/activate
    pip install pulumi pulumi-aws
    ```

6. **Run Pulumi**:
    ```sh
    pulumi up
    ```

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
        "aws-sdk": "^2.1000.0"
      },
      "devDependencies": {},
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
# Use the official Node.js image
FROM public.ecr.aws/lambda/nodejs:20

# Copy function code and dependencies
COPY index.js package*.json ./

# Install dependencies
RUN npm install

# Command to run the Lambda function
CMD ["index.handler"]
```

## Create a Token for Login to Pulumi

1. **Create Pulumi Access Token**:
    - Go to the Pulumi Console at https://app.pulumi.com.
    - Navigate to `Settings` > `Access Tokens`.
    - Click `Create Token`, give it a name, and copy the token.

## Create a GitHub Repo and Set Up Secrets

1. **Create a GitHub Repository**:
    - Navigate to GitHub and create a new repository.

2. **Add GitHub Secrets**:
    - Go to `Settings` > `Secrets and variables` > `Actions`.
    - Add the following secrets:
        - `AWS_ACCESS_KEY_ID`: Your AWS access key ID.
        - `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
        - `PULUMI_ACCESS_TOKEN`: Your Pulumi access token.

## Create S3 Bucket and Set Up Policies

1. **Create S3 Bucket**:
    - Go to the AWS Management Console.
    - Navigate to S3 and create a new bucket. Name it `lambda-function-bucket-poridhi`.

2. **Make the Bucket Public**:
    - Go to the bucket's permissions.
    - Add a bucket policy to make it publicly accessible:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": "*",
          "Action": "s3:GetObject",
          "Resource": "arn:aws:s3:::lambda-function-bucket-poridhi/*"
        }
      ]
    }
    ```

3. **Attach IAM Role to Bucket**:
    - Ensure that the IAM role associated with your GitHub Actions has the necessary permissions to read from and write to the bucket.

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
        run: pulumi login

      - name: Pulumi stack select
        run: pulumi stack select dev7 --cwd infra

      - name: Pulumi up
        run: pulumi up --yes --cwd infra

      - name: Export Pulumi outputs to S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
          S3_BUCKET_NAME: lambda-function-bucket-poridhi
          S3_FILE_NAME: pulumi-outputs.json
        run: |
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
          echo "ECR_REPO_URL=$ECR_REPO_URL" >> $GITHUB_ENV
          echo "ECR_REGISTRY=$ECR_REGISTRY" >> $GITHUB_ENV
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

## Create an API Gateway (HTTP) with AWS Lambda Function

1. **Create API Gateway**:
    - Go to the AWS Management Console.
    - Navigate to API Gateway and create a new HTTP API.

2. **Integrate with Lambda**:
    - Create a new integration with the Lambda function deployed by your GitHub Actions workflow.
    - Deploy the API and note the invoke URL.

## Summary

This documentation provides a detailed guide on setting up an automated workflow to deploy a Node.js Lambda function using Pulumi and GitHub Actions. By organizing infrastructure code in Pulumi and leveraging GitHub Actions for CI/CD, we ensure a smooth and repeatable deployment process.

## Using the API

- Use the API Gateway's invoke URL to test your Lambda function.
- For example, if your API Gateway's invoke URL is `https://api-id.execute-api.us-east-1.amazonaws.com`, you can test it using curl or Postman:
    ```sh
    curl https://api-id.execute-api.us-east-1.amazonaws.com
    ```

By following these steps, you can automate the deployment of a Lambda function, ensuring a consistent and efficient workflow from code changes to deployment.