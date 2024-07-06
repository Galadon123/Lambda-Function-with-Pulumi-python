const initializeTracer = require('./tracing');

// Lambda function handler
exports.handler = async (event) => {
  let response;
  let tracer;

  try {
    // Initialize OpenTelemetry tracing
    tracer = await initializeTracer();

    // Start a span to trace this Lambda function invocation
    const span = tracer.startSpan('lambda-handler');

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
