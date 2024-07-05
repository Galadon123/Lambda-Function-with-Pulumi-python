const awsServerlessExpress = require('aws-serverless-express');
const { initializeAndFetch } = require('./initialization/initialization');
const { app, server } = require('./routes/routes');

// Initialize and fetch before handling requests
initializeAndFetch().catch((error) => {
  console.error("Initializations failed:", error);
  process.exit(1); // Exit Lambda function on initialization failure
});

exports.handler = (event, context) => {
  console.log("Handler invoked");
  return awsServerlessExpress.proxy(server, event, context, 'PROMISE').promise;
};
