# Claude Code Guidelines for Safety Sentinel

This document guides Claude Code and agents working on the Safety Sentinel project. Read and update documentation as you work; the docs are the authoritative source of truth for architecture, API design, and project status.

## Documentation Standards

### Read First
Before implementing a feature or fixing a bug, check these documents for context:
- **[README.MD](README.MD)** — Project vision, product goals, MVP scope, and target users
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design, component responsibilities, data models, and processing flows
- **[API.md](API.md)** — Endpoint specifications, request/response formats, and error handling
- **[DEMOSCRIPT.md](DEMOSCRIPT.md)** — Planned demo walkthrough and key features to showcase

### Update as You Go
When you implement or change code, update the relevant documentation:

- **Architecture changes**: Update [ARCHITECTURE.md](ARCHITECTURE.md) with new components, data flows, or design decisions
- **New or modified endpoints**: Update [API.md](API.md) with request/response examples, query parameters, and error codes
- **Feature additions**: Note the feature in [README.MD](README.MD) if it affects MVP scope or shifts product positioning
- **Demo adjustments**: Update [DEMOSCRIPT.md](DEMOSCRIPT.md) if the walkthrough needs to reflect implementation reality

### How to Update Docs
- Keep documentation concise but complete
- Use the existing markdown structure and formatting
- Link between docs when one references another (e.g., "see [ARCHITECTURE.md](ARCHITECTURE.md#components)")
- Document the WHY behind decisions, not just the WHAT
- Include examples for API endpoints, data models, and processing flows

## Key Architecture Principles

1. **Separation of Concerns**: Frontend (Next.js) → Backend (FastAPI) → Vision Inference → Event Storage
2. **Structured Events**: All safety observations become SafetyEvent records; don't lose information in layers
3. **Rule-Based Processing**: Safety rules should be transparent and testable
4. **Mock-First Alerts**: No real alert delivery in MVP; focus on the workflow demonstration
5. **Hackathon Speed**: Choose simple storage (SQLite) and seeded data over production complexity

## Common Tasks and Documentation

### Adding a New API Endpoint
1. Implement the endpoint in the FastAPI backend
2. Add the endpoint specification to [API.md](API.md) with:
   - HTTP method and path
   - Request body/query parameters with types
   - Response format with example JSON
   - Any error codes it can return
3. Update [ARCHITECTURE.md](ARCHITECTURE.md) if the endpoint touches a new component

### Implementing a Detection Rule
1. Review the current rules in [ARCHITECTURE.md](ARCHITECTURE.md#rule-engine)
2. Add the new rule to the rule engine code
3. Update [ARCHITECTURE.md](ARCHITECTURE.md#rule-engine) with the new rule logic and any severity changes
4. Test with mock detections if the vision model is not yet integrated

### Updating Data Models
1. Review the current model in [ARCHITECTURE.md](ARCHITECTURE.md#data-models) or [API.md](API.md)
2. Implement the change in code (backend/models, frontend/lib/types)
3. Update both [ARCHITECTURE.md](ARCHITECTURE.md) and [API.md](API.md) with the new schema

### Integrating a Vision Model
1. Check [ARCHITECTURE.md](ARCHITECTURE.md#vision-inference-layer) for the preferred and fallback model paths
2. Implement the integration
3. Document the model choice and inference format in [ARCHITECTURE.md](ARCHITECTURE.md#vision-inference-layer)
4. Update the environment variables section if new API keys are needed

## Progress Tracking

- Use [DEMOSCRIPT.md](DEMOSCRIPT.md) to track what is ready for the demo
- Update [README.MD](README.MD) MVP scope section as features are completed
- Mark completed tasks in the relevant doc sections

## Non-Goals and Scope Boundaries

Review the "Non-Goals" and "MVP Scope" sections in [README.MD](README.MD) and [ARCHITECTURE.md](ARCHITECTURE.md) regularly to stay within scope. Don't implement:
- Facial recognition or employee identity matching
- Real alert delivery (Slack, email, SMS)
- Live camera streams
- Automated disciplinary workflows
- Production access control

## When in Doubt

1. Check the relevant doc first
2. Update it if your implementation diverges from the documented design
3. Link to the doc in your commit message so future readers know where the full context lives
