const express = require('express');
const awsServerlessExpress = require('aws-serverless-express');
const awsServerlessExpressMiddleware = require('aws-serverless-express/middleware');
const { trace, context } = require('@opentelemetry/api');
const { traceFunction } = require('./tracing');

const app = express();
const server = awsServerlessExpress.createServer(app);

app.use(express.json());
app.use(awsServerlessExpressMiddleware.eventContext());

// Define your Express routes
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

app.get('/slow', async (req, res) => {
  await traceFunction('GET /slow', async () => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    const activeSpan = trace.getSpan(context.active());
    if (activeSpan) {
      res.send(`This is a slow route. Trace ID: ${activeSpan.spanContext().traceId}`);
    } else {
      res.send('This is a slow route.'); // Fallback response if no active span
    }
  });
});

app.get('/error', async (req, res) => {
  await traceFunction('GET /error', async () => {
    res.status(500).send(`This route returns an error. Trace ID: ${trace.getSpan(context.active()).spanContext().traceId}`);
    trace.getSpan(context.active()).setStatus({ code: 2 }); // Status code 2 represents an error
  });
});

module.exports = {
  app,
  server,
};
