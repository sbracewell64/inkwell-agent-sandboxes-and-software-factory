# ADR-0002 — Define the Sandbox Contract Before Replacing exe.dev

**Status:** Proposed  
**Date:** 2026-08-13

## Context

The proven baseline uses exe.dev, which is a commercial service. A free/local replacement is desired.

The current repository directly encodes exe.dev behavior in host lifecycle recipes.

## Proposed decision

Do not replace individual exe.dev commands ad hoc.

First define a provider-neutral sandbox contract and prove an exe.dev adapter against it. Then implement a local/free adapter.

## Required contract capabilities

- create isolated environment
- establish stable run identity
- stage/clone source
- inject only bounded runtime secrets
- execute commands
- detect readiness
- expose application and observability ports
- inspect liveness/state
- extract artifacts and Git history
- destroy explicitly
- recover after interrupted host processes

## Acceptance

The same lifecycle conformance suite must pass against:

1. exe.dev reference adapter,
2. selected local/free adapter.

## Rationale

This preserves SSSF's semantics while swapping infrastructure, rather than letting the infrastructure provider become the architecture.
