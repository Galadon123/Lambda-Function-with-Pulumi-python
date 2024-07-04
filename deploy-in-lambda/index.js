const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { trace, context } = require('@opentelemetry/api');
const grpc = require('@grpc/grpc-js');
const AWS = require('aws-sdk');
const express = require('express');
const awsServerlessExpress = require('aws-serverless-express');
const awsServerlessExpressMiddleware = require('aws-serverless-express/middleware');

const S3_BUCKET_NAME = 'lambda-function-bucket-poridhi'; // Replace with your S3 bucket name
const S3_FILE_NAME = 'pulumi-outputs.json'; // Replace with your file name

const app = express();
const server = awsServerlessExpress.createServer(app);

app.use(express.json());
app.use(awsServerlessExpressMiddleware.eventContext());

let otelInitialized = false;
let collectorUrl = null;

async function initializeOpenTelemetry() {
  if (!otelInitialized) {
    console.log("Initializing OpenTelemetry...");
    try {
      const traceExporter = new OTLPTraceExporter({
        url: collectorUrl,
        credentials: grpc.credentials.createInsecure(),
      });

      const sdk = new NodeSDK({
        traceExporter,
        instrumentations: [getNodeAutoInstrumentations()],
      });

      await sdk.start();
      otelInitialized = true;
      console.log('OpenTelemetry SDK initialized');
    } catch (error) {
      console.error("Error initializing OpenTelemetry:", error);
      throw error; // Rethrow error to handle at the caller level
    }
  }
}

async function fetchCollectorUrl() {
  try {
    const s3 = new AWS.S3();
    const data = await s3.getObject({ Bucket: S3_BUCKET_NAME, Key: S3_FILE_NAME }).promise();
    const outputs = JSON.parse(data.Body.toString());
    collectorUrl = `http://${outputs.ec2_private_ip}:4317`; // Assuming the port is 4317
    console.log(`Retrieved collector URL from S3: ${collectorUrl}`);
  } catch (error) {
    console.error("Error fetching collector URL from S3:", error);
    throw error; // Rethrow error to handle at the caller level
  }
}

async function initializeAndFetch() {
  try {
    await fetchCollectorUrl();
    await initializeOpenTelemetry();
  } catch (error) {
    console.error("Initialization error:", error);
    // Handle initialization error as needed
    throw error; // Rethrow error to handle at the caller level
  }
}

// Ensure OpenTelemetry and collector URL are initialized before handling requests
initializeAndFetch().catch((error) => {
  console.error("Initialization failed:", error);
  process.exit(1); // Exit Lambda function on initialization failure
});

app.get('/', async (req, res) => {
  await traceFunction('GET /', async () => {
    res.send(`Hello, World! Trace ID: ${trace.getSpan(context.active()).spanContext().traceId}`);
  });
});

app.get('/trace', async (req, res) => {
  await traceFunction('GET /trace', async () => {
    res.send(`This route is traced with OpenTelemetry! Trace ID: ${trace.getSpan(context.active()).spanContext().traceId}`);
  });
});

app.get('/slow', async (req, res) => {
  await traceFunction('GET /slow', async () => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    res.send(`This is a slow route. Trace ID: ${trace.getSpan(context.active()).spanContext().traceId}`);
  });
});

app.get('/error', async (req, res) => {
  await traceFunction('GET /error', async () => {
    const currentSpan = trace.getTracer('default').startSpan('GET /error');
    context.with(trace.setSpan(context.active(), currentSpan), async () => {
      res.status(500).send(`This route returns an error. Trace ID: ${trace.getSpan(context.active()).spanContext().traceId}`);
      currentSpan.setStatus({ code: trace.SpanStatusCode.ERROR });
      currentSpan.end();
    });
  });
});

// Middleware function to handle tracing
async function traceFunction(name, callback) {
  const currentSpan = trace.getTracer('default').startSpan(name);
  context.with(trace.setSpan(context.active(), currentSpan), async () => {
    try {
      await callback();
    } catch (error) {
      console.error(`Error processing ${name}:`, error);
      currentSpan.setStatus({ code: trace.SpanStatusCode.ERROR });
    } finally {
      currentSpan.end();
    }
  });
}

exports.handler = (event, context) => {
  console.log("Handler invoked");
  return awsServerlessExpress.proxy(server, event, context, 'PROMISE').promise;
};
