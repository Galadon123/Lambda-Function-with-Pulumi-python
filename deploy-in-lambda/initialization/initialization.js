const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const grpc = require('@grpc/grpc-js');
const AWS = require('aws-sdk');

const S3_BUCKET_NAME = 'lambda-function-bucket-poridhi'; // Replace with your S3 bucket name
const S3_FILE_NAME = 'pulumi-outputs.json'; // Replace with your file name

let collectorUrl = null;
let otelInitialized = false;

async function fetchCollectorUrl() {
  try {
    const s3 = new AWS.S3();
    const data = await s3.getObject({ Bucket: S3_BUCKET_NAME, Key: S3_FILE_NAME }).promise();
    const outputs = JSON.parse(data.Body.toString());
    collectorUrl = `http://${outputs.ec2_private_ip}:4317`; // Assuming the port is 4317
    console.log(`Retrieved collector URL from S3: ${collectorUrl}`);
  } catch (error) {
    console.error("Error fetching collector URL from S3:", error);
    throw error;
  }
}

async function initializeOpenTelemetry() {
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
    throw error;
  }
}

async function initializeAndFetch() {
  try {
    await fetchCollectorUrl();
    await initializeOpenTelemetry();
  } catch (error) {
    console.error("Initialization failed:", error);
    process.exit(1); // Exit Lambda function on initialization failure
  }
}

module.exports = {
  initializeAndFetch,
};
