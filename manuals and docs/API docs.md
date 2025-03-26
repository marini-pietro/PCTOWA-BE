# Introduction

The first part of this short manual will explain in detail how to reach and communicate correctly with the API and how to correctly parse its response, the second will contain a table with the information of each endpoint.

## Getting Started

To begin using the API, ensure you have the following prerequisites:

1. **API Key**: Obtain your API key.
2. **Environment Setup**: Install the necessary tools and libraries for making HTTP requests (e.g., `curl`, Postman, or a programming language with HTTP support like Python or JavaScript), constants in config.py are correct and the DBMS is running and stable.
3. **Base URL**: Use the base URL provided in the API documentation for all requests.

## Authentication

All API requests must include the API key in the headers for authentication. Below is an example of how to include the API key in a request:

```http
GET /endpoint HTTP/1.1
Host: api.example.com
Authorization: Bearer YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual API key.

## Making Requests

The API supports the following HTTP methods:

- **GET**: Retrieve data from the server.
- **POST**: Send data to the server.
- **PUT**: Update existing data.
- **DELETE**: Remove data from the server.

### Example Request

Here is an example of a `GET` request using `curl`:

```bash
curl -X GET "https://api.example.com/endpoint" -H "Authorization: Bearer YOUR_API_KEY"
```

### Example Response

A successful response will typically look something like this:

```json
{
    "status": "success",
    "data": {
        "id": 123,
        "name": "Example Item",
        "description": "This is an example response."
    }
}
```

## Error Handling

If an error occurs, the API will return an appropriate HTTP status code and a JSON response with details about the error. For example:

```json
{
    "status": "error",
    "message": "Invalid API key provided."
}
```

Refer to the API documentation for a complete list of error codes and their meanings.

## Main API

Base URL, host and port are defined in `config.py`.

## Authentication API

Base URL, host and port are defined in `config.py`.

## Log API

Base URL, host and port are defined in `config.py`.

| Endpoint    | Method | Description           | Input                    | Output      |
|-------------|--------|-----------------------|--------------------------|-------------|
| `/health`   | GET    | Health checkup        | none                     | JSON object |
| `/log`      | POST   | Log provided data     | JSON object              | JSON object |