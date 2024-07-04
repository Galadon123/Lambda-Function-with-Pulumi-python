# Use the official AWS Lambda node image
FROM public.ecr.aws/lambda/nodejs:14

# Copy initialization scripts
COPY initialization.js ./initialization/
COPY routes.js ./routes/

# Copy Lambda function handler
COPY index.js ./

# Install production dependencies (if any)
COPY package.json package-lock.json ./
RUN npm install --only=production

# Command can be overwritten by providing a different command in the template directly.
CMD [ "index.handler" ]
