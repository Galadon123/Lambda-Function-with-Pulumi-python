// tracing.js
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { CollectorTraceExporter } = require('@opentelemetry/exporter-collector');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const AWS = require('aws-sdk');

// Initialize AWS SDK (for interacting with S3)
const s3 = new AWS.S3();
const bucketName = 'lambda-function-poridhi-bucket';
const objectKey = 'pulumi-outputs.json'; // Adjust if needed

// Function to retrieve EC2 private IP from S3 JSON file
const getEc2PrivateIp = async () => {
  const params = {
    Bucket: bucketName,
    Key: objectKey,
  };
  const data = await s3.getObject(params).promise();
  const pulumiOutputs = JSON.parse(data.Body.toString('utf-8'));
  return pulumiOutputs.ec2_private_ip.trim();
};

const initializeTracer = async () => {
  try {
    // Retrieve EC2 private IP dynamically from S3 JSON file
    const ec2PrivateIp = await getEc2PrivateIp();

    // Initialize OpenTelemetry provider
    const provider = new NodeTracerProvider();

    // Configure OpenTelemetry exporter with dynamic IP
    const exporter = new CollectorTraceExporter({
      serviceName: 'my-lambda-function',
      url: `grpc://${ec2PrivateIp}:4317`, // Replace with your OTel collector URL
    });

    // Add span processor and register provider
    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    provider.register();

    console.log('OpenTelemetry initialized successfully.');
    return provider.getTracer('default'); // Return the tracer instance
  } catch (error) {
    console.error('Error initializing OpenTelemetry:', error);
  }
};

module.exports = initializeTracer;
