# Rescue HTTP API design

## Intent and scope

Provide a small local server for the future visual app. It exposes the existing rescue operations, their complete results, the current run state and recorded activity. Runs and call histories live in memory. Accounts, remote access, persistent storage and the web app itself are outside this feature.

## Approaches

- **Polling (selected):** the client requests the current state and reads call history when needed. This keeps the server and its tests small.
- **Live updates:** the server pushes changes. This makes updates more immediate but adds connection management and testing.

## Behaviour

Each run is isolated. Every call addressed to it, including reads, is recorded with its input and complete result. A history read returns entries completed before that read, then its complete response is recorded. This can consume substantial memory after repeated history reads. Existing rescue rules and concurrency guarantees remain in force.

The specification in [spec 011](../../../specs/011-http-api/spec.md) contains the acceptance criteria. The plan must inventory operations and data, define encodings and ordering under concurrency, and select the smallest meaningful tests. The server listens locally by default.
