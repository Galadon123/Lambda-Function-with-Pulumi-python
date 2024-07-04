const { trace, context } = require('@opentelemetry/api');

// Middleware function to handle tracing
async function traceFunction(name, callback) {
  const currentSpan = trace.getTracer('default').startSpan(name);
  return context.with(trace.setSpan(context.active(), currentSpan), async () => {
    try {
      await callback();
    } catch (error) {
      console.error(`Error processing ${name}:`, error);
      currentSpan.setStatus({ code: 2 }); // Status code 2 represents an error
    } finally {
      currentSpan.end();
    }
  });
}

module.exports = {
  traceFunction,
};
