# Use the official AWS Lambda node image
FROM public.ecr.aws/lambda/nodejs:16

# Copy function code
COPY index.js package.json package-lock.json ./

# Install production dependencies
RUN npm install --only=production

# Command can be overwritten by providing a different command in the template directly.
CMD [ "index.handler" ]