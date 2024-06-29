exports.handler = async (event) => {
    console.log("Event: ", event);
    const response = {
        statusCode: 200,
        body: JSON.stringify('hello world from update version! '),
    };
    return response;
};
