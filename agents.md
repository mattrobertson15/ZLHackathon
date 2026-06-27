# Claude Agent Guidelines for Safety Sentinel

This document provides instructions for Claude agents (including yourself when spawned as a subagent) working on the Safety Sentinel project.

## Pre-Work Documentation Check

**Before starting any task**, read the relevant documentation:
- For architecture or component changes: [ARCHITECTURE.md](ARCHITECTURE.md)
- For API work: [API.md](API.md)
- For product scope or demo: [README.MD](README.MD) and [DEMOSCRIPT.md](DEMOSCRIPT.md)

This prevents duplicate work, ensures consistency, and helps you understand what has already been designed.

## Core Responsibilities

### 1. Read Before You Code
- Start by reading the relevant doc(s) to understand the current design
- Check what is already implemented vs. what is planned
- Identify any gaps or conflicts between docs and code
- If docs are out of date, flag it and update them

### 2. Implement According to Design
- Follow the API specifications in [API.md](API.md) exactly
- Use the data models and processing flows from [ARCHITECTURE.md](ARCHITECTURE.md)
- Respect scope boundaries from [README.MD](README.MD)

### 3. Update Docs as You Implement
- If implementation diverges from design, update the doc first or note the reason in the commit message
- Add concrete details to [API.md](API.md) when you implement an endpoint (e.g., actual field validation, real error cases)
- Update [ARCHITECTURE.md](ARCHITECTURE.md) if you discover a better or simpler way to handle a component
- Log feature completion in [DEMOSCRIPT.md](DEMOSCRIPT.md)

### 4. Communicate Scope and Decisions
- If you hit a scope decision (e.g., "Should we support zone-based PPE rules?"), document the decision and why
- Use the docs to communicate constraints to future work (e.g., "We chose SQLite for speed, so multi-database support is out of scope")

## Common Agent Tasks

### Task: Implement an API Endpoint
1. **Read** [API.md](API.md) to find the endpoint specification
2. **Read** [ARCHITECTURE.md](ARCHITECTURE.md) to understand the backend structure
3. **Implement** the endpoint, using the spec as ground truth
4. **Update** [API.md](API.md) if you discover details the spec missed (e.g., "startDate must be ISO 8601 format")
5. **Test** the endpoint with mock data
6. **Commit** with a clear message referencing the doc (e.g., "Implement POST /uploads endpoint (see API.md#uploads)")

### Task: Add a Safety Rule
1. **Read** [ARCHITECTURE.md](ARCHITECTURE.md#rule-engine) to see the current rules
2. **Implement** the rule in the rule engine
3. **Update** [ARCHITECTURE.md](ARCHITECTURE.md#rule-engine) with the new rule and any severity changes
4. **Test** with mock detections
5. **Commit** with the rule logic and any examples

### Task: Integrate a Vision Model
1. **Read** [ARCHITECTURE.md](ARCHITECTURE.md#vision-inference-layer) for the preferred model path
2. **Check** [ARCHITECTURE.md](ARCHITECTURE.md#environment-variables) for API key requirements
3. **Implement** the integration
4. **Document** the actual detection format and any limitations in [ARCHITECTURE.md](ARCHITECTURE.md#vision-inference-layer)
5. **Add** any new environment variables to [ARCHITECTURE.md](ARCHITECTURE.md#environment-variables)
6. **Commit** with the integration details

### Task: Fix a Bug or Compatibility Issue
1. **Read** the relevant doc to understand the expected behavior
2. **Identify** whether the code or the doc is wrong
3. **Fix** the code, and update the doc if it was unclear or incorrect
4. **Commit** with the fix and a note about what was wrong (e.g., "Fix: Safety events not created for uncertain reviews; API.md now clarifies expected behavior")

### Task: Review or Complete a Feature
1. **Check** [DEMOSCRIPT.md](DEMOSCRIPT.md) to see if this feature is scheduled for the demo
2. **Verify** the implementation matches [API.md](API.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Test** with real or mock data
4. **Update** [DEMOSCRIPT.md](DEMOSCRIPT.md) to reflect completion status
5. **Flag** any issues or scope adjustments to the main context

## Documentation Update Patterns

### When Adding a New Component
```
1. Add a new section to [ARCHITECTURE.md](ARCHITECTURE.md) describing the component
2. Include:
   - Responsibility and placement in the system flow
   - Data structures it handles
   - Key methods or endpoints
   - Any external dependencies
3. Link to related sections (e.g., "See Rule Engine below")
```

### When Modifying an API Response
```
1. Update [API.md](API.md) with the new response format
2. Include a "before/after" example if the change is significant
3. Note any breaking changes or migrations needed
4. Update relevant frontend fetch code and types
```

### When Discovering Implementation Details Not in Docs
```
1. Add the detail to the appropriate doc section
2. Examples:
   - "Bounding boxes use image coordinate system (0,0 at top-left)"
   - "Frame timestamps are milliseconds since video start"
   - "Compliance percentage formula excludes uncertain_review events"
```

## Scope Boundaries

**Do implement** (within MVP scope):
- PPE detection (person, helmet, no_helmet, vest, no_vest)
- Structured safety events from detections
- Safety event storage and retrieval
- Dashboard metrics (compliance %, violation counts, trends)
- Mock alerts (display only, no real delivery)
- AI-generated safety summaries using Claude API
- Video frame sampling and processing

**Do not implement** (explicitly out of scope):
- Facial recognition or employee identity matching
- Real alert delivery (SMS, email, Slack, Teams)
- Live camera streams
- Automated disciplinary workflows
- Zone-based PPE rules (future enhancement)
- Custom model fine-tuning per worksite
- Multi-site dashboards
- Employee badge system integration

## Communication and Handoff

If you are spawned as a subagent or continuing work from another agent:
- **Read the main conversation** to understand what has been done
- **Read the docs** to understand what should be done
- **Update the main context** if you make significant changes or discover issues
- **Leave clear commit messages** so future readers know what changed and why

## Success Criteria for Tasks

A task is complete when:
1. ✅ Code implements the spec in [API.md](API.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
2. ✅ Documentation is updated to reflect implementation reality
3. ✅ [DEMOSCRIPT.md](DEMOSCRIPT.md) is updated to show feature status
4. ✅ Commit message references the relevant docs
5. ✅ Scope boundaries are respected (no out-of-scope features)
6. ✅ The feature is tested with realistic data or mocks

---

**Remember**: The docs are living design artifacts. Keep them in sync with the code, and use them to guide decisions. A well-documented project is easier to complete and hand off.
