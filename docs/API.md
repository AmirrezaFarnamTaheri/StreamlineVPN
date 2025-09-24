# API Overview

The StreamlineVPN API provides a comprehensive REST API for accessing merged VPN configurations and system metrics.

## Endpoints

### Configurations

- **GET /api/v1/configurations**
  - **Description**: Retrieve processed and merged VPN configurations.
  - **Query Parameters**:
    - `limit` (int, optional): The maximum number of configurations to return. Default is 100.
    - `offset` (int, optional): The number of configurations to skip. Default is 0.
  - **Response**: A JSON object containing a list of configurations and pagination details.

- **GET /api/export/{format}**
  - **Description**: Export configurations in a specific format.
  - **Path Parameters**:
    - `format` (string, required): The output format. Supported formats: `json`, `clash`, `singbox`, `base64`.
  - **Response**: The configurations in the specified format.

### Sources

- **GET /api/v1/sources**
  - **Description**: List configured source URLs.
  - **Response**: A JSON object containing a list of source URLs.

- **POST /api/v1/sources/validate-urls**
  - **Description**: Validate a list of URLs.
  - **Request Body**: A JSON object with a list of URLs.
    ```json
    {
      "urls": ["http://example.com/sub1", "http://example.com/sub2"]
    }
    ```
  - **Response**: A JSON object with the validation results.

### Pipeline

- **POST /api/v1/pipeline/run**
  - **Description**: Trigger the VPN configuration processing pipeline.
  - **Request Body**: An optional JSON object with a list of output formats.
    ```json
    {
      "formats": ["clash", "singbox"]
    }
    ```
  - **Response**: A JSON object with the job ID and status.

### System

- **GET /health**
  - **Description**: Health check endpoint.
  - **Response**: A JSON object with the system status.

- **GET /api/statistics**
  - **Description**: Get processing statistics.
  - **Response**: A JSON object with detailed statistics.

- **GET /api/jobs**
  - **Description**: Get recent pipeline jobs.
  - **Response**: A JSON object with a list of recent jobs.

- **POST /api/v1/cache/clear**
  - **Description**: Clear the cache.
  - **Response**: A JSON object with the status of the operation.

### Webhooks

- **POST /api/v1/webhooks**
  - **Description**: Create a new webhook.
  - **Request Body**: A JSON object with the webhook URL and event.
    ```json
    {
      "url": "http://example.com/webhook",
      "event": "pipeline_finished"
    }
    ```
  - **Response**: A JSON object with a confirmation message.

- **GET /api/v1/webhooks**
  - **Description**: Get all configured webhooks.
  - **Response**: A JSON object with a list of webhooks.

- **DELETE /api/v1/webhooks**
  - **Description**: Delete a webhook.
  - **Query Parameters**:
    - `url` (string, required): The URL of the webhook to delete.
    - `event` (string, required): The event of the webhook to delete.
  - **Response**: A JSON object with a confirmation message.

## Interactive Documentation

You can access the interactive Swagger UI at `/docs` when the API server is running.
