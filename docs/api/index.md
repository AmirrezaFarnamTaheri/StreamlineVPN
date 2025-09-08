---
layout: default
title: API Documentation
description: A comprehensive guide to the StreamlineVPN REST API.
---

The StreamlineVPN API provides a powerful and flexible interface for interacting with the VPN management platform. It is a RESTful API that uses standard HTTP verbs and returns JSON-encoded responses.

## Authentication

All API requests must be authenticated using a bearer token. You can obtain a token by logging in to the Control Panel. The token should be included in the `Authorization` header of all requests.

```
Authorization: Bearer <your_token>
```

## Endpoints

### Subscriptions

*   `GET /api/v1/sub/raw`: Get the raw subscription data.
*   `GET /api/v1/sub/base64`: Get the Base64 encoded subscription.
*   `GET /api/v1/sub/singbox`: Get the configuration in Sing-box format.
*   `GET /api/v1/sub/clash`: Get the configuration in Clash format.

### System Status

*   `GET /health`: Check the health of the API server.
*   `GET /api/v1/status`: Get the status and statistics of the VPN service.

### Configuration

*   `GET /api/sources`: Get the list of configured VPN sources.
*   `POST /api/process`: Trigger a new processing job for the VPN sources.

For a complete and interactive API reference, please see our [OpenAPI documentation](/api/openapi.html).
