# API Versioning Strategy

This document outlines the versioning strategy for the StreamlineVPN API, ensuring that developers can rely on a stable and predictable interface while allowing for future improvements.

## Guiding Principles

- **Stability**: We prioritize a stable API for our users. Changes will be introduced in a way that minimizes disruption.
- **Clarity**: The versioning scheme is designed to be clear and easy to understand.
- **Predictability**: Developers should be able to anticipate how the API will evolve and when changes will occur.

## Versioning Scheme

The StreamlineVPN API uses a **URL-based versioning** scheme. The API version is included in the URL path, for example:

`/api/v1/...`
`/api/v2/...`

We use a `v` prefix followed by a major version number (e.g., `v1`, `v2`). Minor and patch-level changes, which are always backward-compatible, will not be reflected in the URL.

### Types of Changes

We categorize API changes into three types:

1.  **Backward-Incompatible Changes (Major Version)**: These are changes that may break existing client integrations. Examples include:
    - Removing an endpoint.
    - Renaming a field in the JSON response.
    - Changing the data type of a field.
    - Adding a new required field to a request body.

    When a backward-incompatible change is necessary, we will release a **new major version** of the API (e.g., from `v1` to `v2`).

2.  **Backward-Compatible Changes (Minor Version)**: These are changes that add new functionality without breaking existing integrations. Examples include:
    - Adding a new endpoint.
    - Adding a new, optional field to a request body.
    - Adding a new field to a JSON response.
    - Adding new values to an existing `enum` field.

    These changes will be introduced to the existing API version without changing the version in the URL.

3.  **Bug Fixes (Patch Version)**: These are small, backward-compatible fixes to correct unintended behavior. These changes will also be applied to the current API version.

## Deprecation Policy

When a new major version of the API is released (e.g., `v2`), the previous version (`v1`) will be considered **deprecated**.

- The deprecated version will be supported for a minimum of **6 months** after the new version is released.
- During the deprecation period, we will provide support and bug fixes for critical issues.
- We will actively communicate the deprecation timeline and migration guides to help users transition to the new version.
- After the deprecation period ends, the older version may become unavailable.

## Changelog and Communication

All changes to the API, regardless of their type, will be documented in the API Changelog. We will add a `changelog.md` file to `docs/api` soon.

We will notify developers of upcoming changes and new versions through the following channels:

- The project's official blog.
- A dedicated developer mailing list.
- Announcements on the project's community channels.

We recommend that all developers subscribe to at least one of these channels to stay informed about the API's evolution.
