const initializeTracer = require('./tracing');
const { trace } = require('@opentelemetry/api');

let sdkPromise = initializeTracer();

exports.handler = async (event) => {
  let sdk;
  try {
    sdk = await sdkPromise;
  } catch (error) {
    console.error('Initialization failed:', error);
    return {
      statusCode: 500,
      body: JSON.stringify('Internal Server Error'),
    };
  }

  const tracer = trace.getTracer('default'); // Get the tracer from the OpenTelemetry sss
  const span = tracer.startSpan('lambda-handler');
  try {
    let response;
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

    span.end();
    return response;
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: 2, message: error.message });
    span.end();
    return {
      statusCode: 500,
      body: JSON.stringify('Internal Server Error'),
    };
  }
};
