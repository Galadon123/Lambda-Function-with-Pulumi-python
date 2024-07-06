const AWS = require('aws-sdk');
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { CollectorTraceExporter } = require('@opentelemetry/exporter-collector');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');

// Initialize AWS SDK (for interacting with S3)
const s3 = new AWS.S3();
const bucketName = 'lambda-function-bucket-poridhi';
const objectKey = 'pulumi-outputs.json'; // Adjust if needed

// Function to retrieve EC2 private IP from S3 JSON filessf
const getEc2PrivateIp = async () => {
  const params = {
    Bucket: bucketName,
    Key: objectKey,
  };
  const data = await s3.getObject(params).promise();
  const pulumiOutputs = JSON.parse(data.Body.toString('utf-8'));
  return pulumiOutputs.ec2_private_ip.trim();
};

// Lambda function handler
exports.handler = async (event) => {
  let response;

  try {
    // Retrieve EC2 private IP dynamically from S3 JSON file
    const ec2PrivateIp = await getEc2PrivateIp();
    console.log('EC2 Private IP retrieved:', ec2PrivateIp);

    // Initialize OpenTelemetry provider
    const provider = new NodeTracerProvider();

    // Configure OpenTelemetry exporter with dynamic IP
    const exporter = new CollectorTraceExporter({
      serviceName: 'my-lambda-function',
      url: `http://${ec2PrivateIp}:4317`, // Replace with your OTel collector URL
    });

    // Add span processor and register provider
    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    provider.register();

    // Start a span to trace this Lambda function invocation
    const span = provider.getTracer('default').startSpan('lambda-handler');

    // Handle incoming HTTP requests
    switch (event.httpMethod) {
      case 'GET':
        if (event.path === '/default/my-lambda-function') {
          response = {
            statusCode: 200,
            body: JSON.stringify('Hello from Lambda!'),
          };
        } else if (event.path === '/default/my-lambda-function/test1') {
          response = {
            statusCode: 200,
            body: JSON.stringify('This is test1 route!'),
          };
        } else if (event.path === '/default/my-lambda-function/test2') {
          response = {
            statusCode: 200,
            body: JSON.stringify('This is test2 route!'),
          };
        } else {
          response = {
            statusCode: 404,
            body: JSON.stringify('Not Found'),
          };
        }
        break;
      default:
        response = {
          statusCode: 405,
          body: JSON.stringify('Method Not Allowed'),
        };
    }

    // End the span for this Lambda function invocation
    span.end();
    console.log('Ended span with trace ID:', span.spanContext().traceId);

    return response;
  } catch (error) {
    // Handle errors gracefully
    console.error('Error:', error);

    // Return an error response
    return {
      statusCode: 500,
      body: JSON.stringify('Internal Server Error'),
    };
  }
};
