# RecoverX

RecoverX is an AI-powered revenue recovery system for merchants designed to detect revenue at risk from failed payments, checkout abandonment, and subscription or billing failures, diagnose underlying causes, select bounded recovery interventions, execute actions through payment gateways such as Razorpay Test Mode APIs, verify outcomes, and maintain a comprehensive audit trail.

## Development Status

**Phase 0 - Project Setup**

The repository has been initialized with the foundational directory structure and baseline configuration. No application dependencies, database schemas, agent workflows, or frontend code have been implemented yet.

## Planned Architecture

At a high level, RecoverX is designed around a modular, multi-tier agentic architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       RecoverX Frontend                     │
│   (Merchant Dashboard, Recovery Metrics, Audit Trails UI)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / WebSocket
┌──────────────────────────────▼──────────────────────────────┐
│                       RecoverX Backend                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                     API Gateway & Core                │  │
│  └───────────┬───────────────────────────────┬───────────┘  │
│              │                               │              │
│  ┌───────────▼───────────┐       ┌───────────▼───────────┐  │
│  │   AI Agent Orchestrator│       │    Execution Engine   │  │
│  │   - Failure Diagnostic│       │    - Razorpay Test API│  │
│  │   - Bounded Actions   │       │    - Retries & Links  │  │
│  └───────────┬───────────┘       └───────────┬───────────┘  │
│              │                               │              │
│  ┌───────────▼───────────────────────────────▼───────────┐  │
│  │           Audit Logging & State Management            │  │
│  └───────────────────────────┬───────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Data & Storage Layer                     │
│     (PostgreSQL Database / Redis Queue / Synthetic Data)    │
└─────────────────────────────────────────────────────────────┘
```

### Component Overview

- **Frontend (`frontend/`)**: Merchant-facing user interface for monitoring recovered revenue, managing customer cohorts, reviewing diagnostic reports, and viewing end-to-end agent decision audit logs.
- **Backend (`backend/`)**: Core application services containing:
  - **Diagnostic & Agent Engine**: Analyzes failure signals and selects bounded recovery strategies according to safety guardrails.
  - **Execution Engine**: Integrates with merchant payment processors (Razorpay Test Mode APIs) to trigger smart retries, payment links, and customer communication workflows.
  - **Audit & Verification Service**: Verifies transaction state changes and maintains immutable audit records for each recovery attempt.
- **Data Layer (`data/`)**: Repository for synthetic event generation (`data/synthetic/`), test fixtures, schemas, and persistence models.
- **Docs (`docs/`)**: System architecture documentation, API specifications, and agent guardrail guidelines.
- **Scripts (`scripts/`)**: Setup utilities, benchmark suites, and synthetic data generators.
