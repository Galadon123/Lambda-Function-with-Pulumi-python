# Use the official Node.js image
FROM public.ecr.aws/lambda/nodejs:20

# Copy function code and dependencies
COPY index.js package*.json ./

# Install dependencies
RUN npm install

# Command to run the Lambda function
CMD ["index.handler"]