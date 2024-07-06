const initializeTracer = require('./tracing');

exports.handler = async (event) => {
  let response;
  let tracer;
  let span;

  try {
    tracer = await initializeTracer();
    span = tracer.startSpan('lambda-handler');

    // Set the current span as active
    tracer.startActiveSpan('lambda-handler', async (parentSpan) => {
      try {
        switch (event.httpMethod) {
          case 'GET':
            if (event.path === '/default/my-lambda-function') {
              tracer.startActiveSpan('handle-default-route', (routeSpan) => {
                response = {
                  statusCode: 200,
                  body: JSON.stringify('Hello from Lambda!'),
                };
                routeSpan.end();
              });
            } else if (event.path === '/default/my-lambda-function/test1') {
              tracer.startActiveSpan('handle-test1-route', (routeSpan) => {
                response = {
                  statusCode: 200,
                  body: JSON.stringify('This is test1 route!'),
                };
                routeSpan.end();
              });
            } else if (event.path === '/default/my-lambda-function/test2') {
              tracer.startActiveSpan('handle-test2-route', (routeSpan) => {
                response = {
                  statusCode: 200,
                  body: JSON.stringify('This is test2 route!'),
                };
                routeSpan.end();
              });
            } else {
              tracer.startActiveSpan('handle-not-found', (routeSpan) => {
                response = {
                  statusCode: 404,
                  body: JSON.stringify('Not Found'),
                };
                routeSpan.end();
              });
            }
            break;
          default:
            tracer.startActiveSpan('method-not-allowed', (methodSpan) => {
              response = {
                statusCode: 405,
                body: JSON.stringify('Method Not Allowed'),
              };
              methodSpan.end();
            });
        }
      } finally {
        parentSpan.end();
      }
    });

    return response;
  } catch (error) {
    console.error('Error:', error);
    if (tracer) {
      tracer.startActiveSpan('error-handler', (errorSpan) => {
        errorSpan.recordException(error);
        errorSpan.end();
      });
    }
    return {
      statusCode: 500,
      body: JSON.stringify('Internal Server Error'),
    };
  }
};