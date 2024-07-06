const initializeTracer = require('./tracing');

exports.handler = async (event) => {
  let response;
  let tracer;

  try {
    tracer = await initializeTracer();
    const span = tracer.startSpan('lambda-handler');

    // Use a context to propagate the span
    await tracer.withSpan(span, async () => {
      switch (event.httpMethod) {
        case 'GET':
          if (event.path === '/default/my-lambda-function') {
            const routeSpan = tracer.startSpan('handle-default-route');
            response = {
              statusCode: 200,
              body: JSON.stringify('Hello from Lambda!'),
            };
            routeSpan.end();
          } else if (event.path === '/default/my-lambda-function/test1') {
            const routeSpan = tracer.startSpan('handle-test1-route');
            response = {
              statusCode: 200,
              body: JSON.stringify('This is test1 route!'),
            };
            routeSpan.end();
          } else if (event.path === '/default/my-lambda-function/test2') {
            const routeSpan = tracer.startSpan('handle-test2-route');
            response = {
              statusCode: 200,
              body: JSON.stringify('This is test2 route!'),
            };
            routeSpan.end();
          } else {
            const routeSpan = tracer.startSpan('handle-not-found');
            response = {
              statusCode: 404,
              body: JSON.stringify('Not Found'),
            };
            routeSpan.end();
          }
          break;
        default:
          const methodNotAllowedSpan = tracer.startSpan('method-not-allowed');
          response = {
            statusCode: 405,
            body: JSON.stringify('Method Not Allowed'),
          };
          methodNotAllowedSpan.end();
      }
    });

    span.end();
    return response;
  } catch (error) {
    console.error('Error:', error);
    if (tracer) {
      const errorSpan = tracer.startSpan('error-handler');
      errorSpan.recordException(error);
      errorSpan.end();
    }
    return {
      statusCode: 500,
      body: JSON.stringify('Internal Server Error'),
    };
  }
};

