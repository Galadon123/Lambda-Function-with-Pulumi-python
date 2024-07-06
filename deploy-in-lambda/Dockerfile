# Use the official AWS Lambda Node.js 14.x image
FROM public.ecr.aws/lambda/nodejs:20

# Copy function code
COPY index.js package.json package-lock.json /var/task/

# Install production dependencies
RUN npm install --production

# Set the CMD to your handler (adjust if your handler file or function name is different)
CMD [ "index.handler" ]
