# Dynamic AI Firewall: Frontend Specification

SaaS Console for SOC Analysts, Security Managers and Administrators

Version 1.0 | October 24, 2026 | Status: Draft for review

## 1. Purpose and Scope

This document defines the frontend of the Dynamic AI Firewall SaaS platform: the web console that customers use to monitor traffic, triage alerts, understand AI decisions, approve automated actions, manage policy and produce compliance evidence. It also covers the separate operator console used by the platform team.

In scope: user roles, screens, user flows, technology stack, multi-tenancy behavior, security, accessibility, performance, testing, release process and roadmap.

Out of scope: the sensor agent, the RL and anomaly detection engines, and the backend services, except where the frontend depends on their API contract.

## 2. Product Context and Assumptions

- The product is a multi-tenant SaaS. Target customers are government bodies, banks, fintechs and telecoms, with Ethiopian institutions as the first market.
- A lightweight sensor is installed in the customer network. Inline enforcement decisions are made at the edge, not in the cloud. The console is a management, investigation and governance plane, never in the packet path.
- The AI operates under a tiered autonomy model: Monitor only, Recommend, Supervised (human approval), and Automatic. New tenants start in Monitor only.
- Every AI decision carries a plain-language explanation, a confidence value, a novelty indicator and a MITRE ATT&CK mapping where applicable.
- Government and bank buyers may require region-pinned data and identity. The frontend must support regional deployments.
- Package versions in this document are not pinned. The team must choose current stable releases at project start and verify them.

## 3. Users and Roles

| Role | Primary goals | Access |
|---|---|---|
| SOC Analyst | Triage alerts, investigate, approve or reject AI actions | Alerts, incidents, approvals, live feed, sensors (read) |
| Security or IT Manager | Posture, trends, policy, compliance reporting | Dashboards, policy, reports, autonomy settings |
| Tenant Admin | Users, SSO, API keys, integrations, billing | All tenant features plus administration |
| Auditor (read-only) | Gather evidence for regulators and audits | Audit log and reports only |
| Platform Operator | Fleet health, tenant support, model rollout | Separate operator console only |

Permissions are enforced by the backend. The frontend hides unavailable controls for clarity but is never the enforcement point.

## 4. Information Architecture and Screens

### 4.1 Tenant Console

1. **Overview.** Threat level, alerts by severity, items needing action, sensor health, blocked versus flagged counts, mean time to triage. Limited to a small number of actionable widgets.
2. **Alert Queue (core screen).** Virtualized, sortable and filterable table, grouped by incident. Columns include severity, ATT&CK technique, confidence, novelty score, source, asset, status and age. Saved views and bulk actions.
3. **Incident Detail.** Timeline, involved flows and assets, the explanation panel (top contributing features, similar past events, ATT&CK mapping, recommended action), notes, assignment and action buttons.
4. **Approvals.** Queue of AI-recommended actions awaiting human sign-off, with impact preview, expiry and one-click reject.
5. **Live Feed.** Real-time stream with pause, filter and rate indicators. Not the home page.
6. **Assets and Network Map.** Topology, sensor locations, lateral movement paths with ATT&CK stage overlays.
7. **Policy.** Static rules and AI-generated rules, per-action autonomy level, allowlists, scheduled maintenance windows and a global kill switch that forces monitor-only mode.
8. **Sensors and Models.** Sensor status, version, last check-in, model version, shadow and canary status, rollback request.
9. **Reports and Compliance.** PCI DSS, ISO 27001 and national regulator oriented evidence packs, scheduled exports as PDF and CSV.
10. **Audit Log.** Immutable, searchable record of every human and AI action, exportable.
11. **Settings.** Users and roles, SSO, SCIM, API keys, webhooks, SIEM integrations, notification channels, data region display.
12. **Billing and Contract.** Plan, usage metering, invoices. Supports invoice and purchase-order payment as well as card.

### 4.2 Public and Onboarding Surfaces

- Marketing site, documentation, trust center, status page link.
- Signup or invitation flow and the organization setup wizard.

### 4.3 Operator Console (separate application)

Tenant list and health, sensor fleet status, model rollout and rollback per tenant, support access with time-limited and logged impersonation, usage and revenue overview. Deployed separately with stricter network and access controls.

## 5. Key User Flows

### 5.1 Onboarding and Sensor Enrollment

1. Admin accepts invitation, sets up MFA or passkey.
2. Organization wizard: name, region, timezone, language, SSO configuration.
3. Sensor enrollment: generate a one-time token, show install command, display live status "waiting for first data", then confirmation with first health check.
4. The tenant is placed in Monitor only mode. A guided checklist explains how and when to raise autonomy.

Success measure: time from signup to first visible telemetry.

### 5.2 Alert Triage

1. Analyst opens the Alert Queue, defaulting to "needs action".
2. Selects an incident, reads the explanation and evidence.
3. Chooses: confirm threat, mark false positive, escalate, or request approval for an action.
4. Feedback is recorded and sent to the learning pipeline, with the analyst identity and timestamp in the audit log.

### 5.3 Approving an AI Action

1. Approval request appears with action type, target, impact preview (for example, number of active sessions affected), confidence and expiry.
2. Approver re-authenticates for destructive actions such as quarantine.
3. Action executes or is rejected. Result and the approver are logged.
4. A visible undo or rollback is available where technically possible.

### 5.4 Kill Switch

A manager or admin can place the whole tenant into Monitor only mode in one confirmed step. The state is shown as a persistent banner on every screen until cleared.

## 6. Technology Stack

| Area | Choice | Rationale |
|---|---|---|
| Framework | Next.js (App Router) with TypeScript | One codebase for public site, docs, onboarding and console, with server-side rendering for public pages |
| Styling and components | Tailwind CSS, shadcn/ui on Radix primitives | Accessible components owned in the codebase, no vendor lock-in |
| Server state | TanStack Query | Caching, retries, pagination |
| Client state | Zustand | Small, simple state for filters and selection |
| Tables | TanStack Table with virtualization | Alert and log tables can reach millions of rows |
| Charts | Apache ECharts | Strong large time-series support |
| Maps | MapLibre GL | Open source, avoids per-load fees |
| Large graph view | Sigma.js or deck.gl (WebGL), Cytoscape.js for small graphs | Attack-path graphs beyond a few thousand nodes |
| Real time | WebSocket for alerts, SSE for simple streams | Matches backend streaming |
| Forms | React Hook Form with Zod | Shared validation schemas |
| API client | Generated from OpenAPI (for example openapi-typescript) | Keeps frontend and FastAPI types in sync |
| Authentication | OIDC provider with SAML and OIDC SSO, SCIM, passkeys; Keycloak when identity must be self-hosted or region-pinned, managed provider acceptable for early pilots | Data residency for government tenants |
| Billing | Stripe Billing and Customer Portal, plus invoice support | Subscriptions, usage metering |
| Feature flags | Unleash or equivalent | Per-tenant and per-plan rollout |
| Internationalization | next-intl | English and Amharic |
| Observability | OpenTelemetry, Sentry, Grafana | Trace slow screens, catch errors |
| Testing | Vitest, React Testing Library, Playwright, Storybook | Unit, component, end-to-end, visual review |
| Hosting | Kubernetes or a managed platform behind CDN and WAF, regional deployments | Edge delivery with data-region control |

## 7. Multi-Tenancy in the Frontend

- The tenant is resolved from the authenticated session and the subdomain (for example `bank-a.example.com`). The client never supplies a tenant identifier that the backend trusts.
- Per-tenant settings: branding, timezone, language, data-region indicator, plan and feature flags.
- Cached data is namespaced by tenant and user. Cache is cleared on logout and tenant switch.
- Automated tests must prove that one tenant cannot view another tenant's data through any route, API call or cache.
- Support staff access to a tenant is time-limited, requires tenant consent, shows a visible banner to the support user and is written to the tenant audit log.

## 8. Design Principles and UX Requirements

1. **Explainability is a first-class component.** Every AI decision shows reasons, evidence, confidence and a novelty indicator. Uncertainty is displayed honestly, with no false precision.
2. **Reduce alert fatigue.** Group related alerts, default to action-needed views, show counts and trends instead of raw noise.
3. **Dangerous actions are deliberate and reversible.** Impact preview, confirmation, re-authentication, automatic expiry and visible rollback.
4. **Clear attribution.** Every historical action is labeled as human or AI, with the actor and reason.
5. **Analyst efficiency.** Dark theme and dense layouts by default, keyboard shortcuts, a command palette and saved views.
6. **Honest degraded states.** If the live stream disconnects or data is stale, show a persistent warning. Never display stale data silently.
7. **Calibrated language.** The interface says "anomalous" or "suspicious" when that is what the system knows, and "confirmed" only after human or external confirmation.

## 9. Real-Time Architecture

- A single multiplexed WebSocket connection per session, authenticated with a short-lived token and refreshed before expiry.
- Server sends batched updates. The client applies backpressure, caps the in-memory buffer, and drops to a "high volume, summarizing" mode when the rate exceeds a threshold.
- Reconnection with exponential backoff and a resume token so missed events can be fetched.
- Heavy client-side filtering runs in a Web Worker.
- Tables are virtualized. No unbounded DOM growth.

## 10. Frontend Security Requirements

- Session tokens in httpOnly, Secure, SameSite cookies. No tokens in localStorage.
- Strict Content Security Policy with no inline scripts, no unsafe-eval, Subresource Integrity on any third-party asset, and no analytics or trackers that send tenant data to third parties.
- CSRF protection on all state-changing requests.
- **Traffic-derived data is hostile input.** Hostnames, user agents, URLs and payload snippets can contain attacker-controlled content. Always escape, never render as HTML, and render with sanitization where rich display is unavoidable. This prevents stored cross-site scripting through the logs.
- Re-authentication or step-up for sensitive actions (approve quarantine, change autonomy level, create API key, disable kill switch).
- Idle session timeout configurable per tenant, with absolute session lifetime.
- Dependency hygiene: lockfiles, automated vulnerability scanning, a software bill of materials (SBOM) for each release, and review of new dependencies.
- Security headers: HSTS, X-Content-Type-Options, frame-ancestors restriction, strict referrer policy.
- Secrets are never in the client bundle. Environment-specific configuration is injected at runtime.
- Independent penetration test of the console before the first production customer.

## 11. Accessibility and Localization

- Target WCAG 2.2 AA. Full keyboard operation, visible focus, sufficient contrast in both themes, screen reader labels on charts and tables, and no information conveyed by color alone.
- English at launch. Amharic as a planned language, with the Ethiopic script supported in fonts, search, exports and PDF reports. Date and number formats follow locale. Right-to-left support is not required for either language but the layout should not preclude it.
- All user-facing strings externalized from the first commit.

## 12. Performance Targets

| Metric | Target |
|---|---|
| Alert queue first render (typical tenant) | Under 2 seconds on a normal broadband connection |
| Interaction latency on filters and sorts | Under 200 ms for loaded data |
| Live alert delay (event to screen) | Under 2 seconds at normal load |
| Console JavaScript budget per route | Defined at project start, enforced in CI |
| Availability of console | Aligned with platform SLA, with graceful read-only degradation |

Targets are initial goals and must be validated with measurement on realistic tenant data volumes.

## 13. API Contract and Integration

- A single OpenAPI specification is the source of truth. Types and the client are generated from it in CI. Breaking changes require a version bump.
- The frontend is built against a mocked API (for example MSW or a FastAPI stub) so UI work is not blocked by detection engineering.
- Pagination is cursor-based. Large exports are asynchronous jobs with a status endpoint.
- Explanation payloads follow an agreed schema: decision, confidence, novelty, primary reason, evidence list, ATT&CK technique, similar past event count, recommended action, model version.
- Integrations exposed in the UI: webhooks, Splunk, QRadar, email and chat notifications.

## 14. Testing Strategy

| Level | Tooling | Coverage |
|---|---|---|
| Unit and component | Vitest, React Testing Library | Logic, forms, explanation rendering |
| Visual and design review | Storybook | Components in isolation, states, themes |
| End-to-end | Playwright | Onboarding, triage, approval, kill switch, role restrictions |
| Tenant isolation | Dedicated Playwright and API suites with two seeded tenants | Cross-tenant access attempts must fail |
| Security | Dependency scanning, static analysis, XSS tests with hostile log payloads, penetration test | Section 10 requirements |
| Accessibility | Automated checks plus manual screen reader review | WCAG 2.2 AA |
| Performance | Lighthouse CI and load tests with large datasets | Section 12 targets |

## 15. Observability, Release and Operations

- CI pipeline: lint, type check, unit tests, build, security scan, SBOM, end-to-end tests, then deploy to staging.
- Progressive delivery: feature flags per tenant and plan, canary releases, instant rollback.
- Frontend error and performance monitoring with tenant-safe data scrubbing (no traffic payloads in error reports).
- Public status page and in-app incident banners. Changelog visible in the console.
- Environments: development, staging with synthetic tenants, production by region.

## 16. Suggested Project Structure

```
frontend/
  app/
    (public)/            marketing, docs, trust center
    (auth)/              login, invitation, MFA
    (console)/
      overview/
      alerts/
      incidents/[id]/
      approvals/
      live/
      assets/
      policy/
      sensors/
      reports/
      audit/
      settings/
      billing/
  components/
    ui/                  shadcn components
    alerts/
    explainability/      reasons, evidence, ATT&CK panels
    charts/
    graph/
  lib/
    api/                 generated OpenAPI client
    realtime/            WebSocket hooks
    auth/
    rbac/
    tenant/
  i18n/                  en, am
  tests/                 unit, e2e, isolation
  .storybook/
operator-console/        separate application
```

## 17. Roadmap

| Phase | Scope |
|---|---|
| Phase 1: Foundation | Tenant-aware shell, authentication, roles, subdomain routing, design tokens, mocked API, CI pipeline |
| Phase 2: Onboarding | Signup, organization wizard, sensor enrollment, first-run Monitor only mode |
| Phase 3: Core loop | Alert queue, incident detail, explanation panel, feedback, audit log |
| Phase 4: Governance | Approvals, autonomy settings, kill switch, policy screens |
| Phase 5: Operations | Overview, sensor and model health, live feed, notifications, integrations |
| Phase 6: Commercial | Billing, usage metering, SSO and SCIM, reports and compliance exports, trust center, status page |
| Phase 7: Operator console | Tenant and fleet management, model rollout controls, audited support access |
| Phase 8: Advanced | AI investigation copilot with approval gates, detection-as-code with simulation against historical traffic, replay and what-if for model versions, case management and shift handoff, large-scale attack-path graph |

The first pilot should be possible at the end of Phase 4, in detection-only mode.

## 18. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Tenant data leakage through UI or cache | Server-resolved tenant, namespaced caches, mandatory isolation tests |
| Stored XSS via traffic-derived data | Escape by default, sanitization, CSP, dedicated tests |
| Operator or control plane compromise affecting many tenants | Separate operator app, step-up auth, signed policy changes, tenant-controlled kill switch |
| Alert overload reduces trust in the product | Grouping, thresholds, feedback loop, honest confidence display |
| Over-promising AI capability | Calibrated wording, explanation panel, human approval tiers |
| Data residency conflicts for government tenants | Regional deployments, region-pinned identity option |
| UI scope outpaces detection quality | Phase gating; advanced features only after the core loop is proven in a pilot |

## 19. Open Decisions

1. Hosting model and first region: single cloud region first, or an Ethiopia-based region for government pilots.
2. Identity provider: managed for early pilots, or self-hosted Keycloak from the start.
3. Amharic in the first release, or English only.
4. Tenant branding: white-labeled subdomains for each customer, or a single branded console.
5. Whether a mobile companion (push alerts and approvals) is needed after Phase 5.
6. Payment methods required at launch: card only, or invoice and purchase order for institutional buyers.

## 20. Reference Standards

The frontend design supports evidence for the following frameworks, which should be verified against the current published versions before use in customer documents: ISO/IEC 27001, NIST Cybersecurity Framework 2.0, PCI DSS v4.0, MITRE ATT&CK, OWASP Top 10 and ASVS, and WCAG 2.2. National requirements from the National Bank of Ethiopia and INSA must be confirmed directly from the issuing bodies.
