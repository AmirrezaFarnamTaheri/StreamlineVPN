# GraphQL API Documentation

## Overview

The VPN Subscription Merger provides a comprehensive GraphQL API for advanced querying, real-time subscriptions, and job management. The GraphQL API is built using Strawberry and provides type-safe operations with real-time updates.

## Endpoint

```
POST /graphql
```

## Schema

The GraphQL schema includes three main operation types:
- **Queries**: Read operations for retrieving data
- **Mutations**: Write operations for creating and modifying data
- **Subscriptions**: Real-time data streams

## Types

### VPNConfig

Represents a VPN configuration with quality metrics and metadata.

```graphql
type VPNConfig {
  id: String!
  host: String!
  port: Int!
  protocol: String!
  quality_score: Float!
  latency_ms: Float
  created_at: DateTime!
  updated_at: DateTime!
}
```

### JobStatus

Represents the status of a background processing job.

```graphql
type JobStatus {
  id: String!
  status: String!
  total_configs: Int!
  valid_configs: Int!
  progress: Float!
}
```

### MergeResult

Result of a merge operation.

```graphql
type MergeResult {
  id: String!
  total_configs: Int!
  valid_configs: Int!
  processing_time: Float!
}
```

## Queries

### health

Check the health status of the GraphQL API.

```graphql
query HealthCheck {
  health
}
```

**Response:**
```json
{
  "data": {
    "health": "ok"
  }
}
```

### job

Get the status of a specific job by ID.

```graphql
query GetJob($id: String!) {
  job(id: $id) {
    id
    status
    total_configs
    valid_configs
    progress
  }
}
```

### configs

Get VPN configurations with filtering and sorting options.

```graphql
query GetConfigs(
  $limit: Int
  $offset: Int
  $protocol: String
  $host_regex: String
  $reachable: Boolean
  $sort: String
  $sources: [String!]
) {
  configs(
    limit: $limit
    offset: $offset
    protocol: $protocol
    host_regex: $host_regex
    reachable: $reachable
    sort: $sort
    sources: $sources
  ) {
    id
    host
    port
    protocol
    quality_score
    latency_ms
    created_at
    updated_at
  }
}
```

## Mutations

### startMerge

Start a new merge operation with specified sources.

```graphql
mutation StartMerge($sources: [String!]) {
  startMerge(sources: $sources) {
    id
    total_configs
    valid_configs
    processing_time
  }
}
```

### cancelJob

Cancel a running job.

```graphql
mutation CancelJob($id: String!) {
  cancelJob(id: $id)
}
```

## Subscriptions

### jobStatus

Subscribe to real-time updates for a specific job.

```graphql
subscription JobStatus($job_id: String!) {
  jobStatus(job_id: $job_id) {
    id
    status
    total_configs
    valid_configs
    progress
  }
}
```

## Error Handling

GraphQL errors are returned in the standard GraphQL error format:

```json
{
  "errors": [
    {
      "message": "Invalid job ID",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "path": [
        "job"
      ],
      "extensions": {
        "code": "JOB_NOT_FOUND"
      }
    }
  ]
}
```

## Rate Limiting

GraphQL operations are subject to the same rate limiting as REST endpoints:
- 100 requests per minute for queries
- 10 requests per minute for mutations
- 5 concurrent subscriptions per client