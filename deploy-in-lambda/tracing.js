
// tracing.js
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { CollectorTraceExporter } = require('@opentelemetry/exporter-collector');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const AWS = require('aws-sdk');

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
    const provider = new NodeTracerProvider();
    const exporter = new CollectorTraceExporter({
      serviceName: 'my-lambda-function',
      url: `http://34.201.69.207:4317`,
    });
    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    provider.register();
    console.log('OpenTelemetry initialized successfully.');
    return provider.getTracer('default');
  } catch (error) {
    console.error('Error initializing OpenTelemetry:', error);
  }
};

module.exports = initializeTracer;

// Lambda function
