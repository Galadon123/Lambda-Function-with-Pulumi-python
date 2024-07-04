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
