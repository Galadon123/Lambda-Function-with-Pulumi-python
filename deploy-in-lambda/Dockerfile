# Use the official AWS Lambda Node.js 20 image
FROM public.ecr.aws/lambda/nodejs:20

# Copy function code and necessary files
COPY index.js tracing.js package.json package-lock.json /var/task/

# Install production dependencies
RUN npm install --production

# Set the CMD to your handler (adjust if your handler file or function name is different)
CMD [ "index.handler" ]





