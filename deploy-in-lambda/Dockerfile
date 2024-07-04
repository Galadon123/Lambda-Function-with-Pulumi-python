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
