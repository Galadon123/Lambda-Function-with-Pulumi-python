const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { AWS } = require('aws-sdk');

const s3 = new AWS.S3();
const bucketName = 'lambda-function-bucket-poridhi';
const objectKey = 'pulumi-outputs.json';

const getEc2PrivateIp = async () => {
  const params = { Bucket: bucketName, Key: objectKey };
  const data = await s3.getObject(params).promise();
  const pulumiOutputs = JSON.parse(data.Body.toString('utf-8'));
  return pulumiOutputs.ec2_private_ip.trim();
};

const initializeTracer = async () => {
  try {
    const ec2PrivateIp = await getEc2PrivateIp();
    const exporter = new OTLPTraceExporter({
      url: `grpc://${ec2PrivateIp}:4317`,
    });

    const sdk = new NodeSDK({
      traceExporter: exporter,
      instrumentations: [getNodeAutoInstrumentations()],
    });

    await sdk.start();
    console.log('OpenTelemetry SDK initialized successfully.');
    return sdk; // Return the SDK
  } catch (error) {
    console.error('Error initializing OpenTelemetry:', error);
    throw error;
  }
};

module.exports = initializeTracer;
