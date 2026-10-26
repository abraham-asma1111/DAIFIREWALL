# Dynamic AI Firewall - Frontend Development Roadmap

**Based on:** Dynamic AI Firewall Frontend Specification v1.0  
**Timeline:** 12-week implementation plan  
**Current Status:** Foundation (Phase 1) - Basic Next.js structure created

---

## Overview

This roadmap breaks down the enterprise-grade SaaS console into manageable sprints. Each phase builds on the previous, with clear deliverables and acceptance criteria.

**Key Principle:** Build the core detection loop first, then add governance and operational features.

---

## Phase 1: Foundation (Weeks 1-2)

### Goals
- Project scaffolding
- Authentication infrastructure
- Multi-tenant routing
- Design system
- CI/CD pipeline

### Tasks

#### Week 1: Project Setup
- [x] Next.js project initialized with TypeScript
- [ ] Install core dependencies:
  - Tailwind CSS ✓
  - shadcn/ui components (Radix primitives)
  - TanStack Query
  - Zustand
  - React Hook Form + Zod
  - next-intl (i18n)
- [ ] Setup project structure:
  ```
  dashboard/
    app/
      (public)/     # Marketing, docs
      (auth)/       # Login, signup
      (console)/    # Main app
    components/
      ui/           # shadcn components
      alerts/
      charts/
      explainability/
    lib/
      api/
      auth/
      tenant/
  ```
- [ ] Configure TypeScript strict mode
- [ ] Setup ESLint + Prettier
- [ ] Create design tokens (colors, spacing, typography)

#### Week 2: Authentication & Routing
- [ ] Authentication setup:
  - [ ] OIDC/OAuth2 integration (Keycloak or Auth0)
  - [ ] Session management (httpOnly cookies)
  - [ ] MFA support
  - [ ] Passkey support preparation
- [ ] Multi-tenant routing:
  - [ ] Subdomain resolution (tenant-a.example.com)
  - [ ] Tenant context provider
  - [ ] Tenant data isolation verification
- [ ] RBAC foundation:
  - [ ] Role definitions (SOC Analyst, Manager, Admin, Auditor)
  - [ ] Permission checking utilities
  - [ ] Protected route wrapper
- [ ] CI/CD pipeline:
  - [ ] GitHub Actions or GitLab CI
  - [ ] Lint, type-check, test on PR
  - [ ] Build and deploy to staging
  - [ ] SBOM generation

**Deliverables:**
- Working auth flow (login/logout)
- Tenant-aware routing
- Design system documented in Storybook
- CI pipeline running

**Acceptance Criteria:**
- User can log in with email/password
- Session persists across page reload
- Tenant is correctly resolved from subdomain
- No cross-tenant data leakage (verified by test)

---

## Phase 2: Onboarding (Weeks 3-4)

### Goals
- User signup and invitation flow
- Organization setup wizard
- Sensor enrollment process
- First-run experience

### Tasks

#### Week 3: Signup & Organization Setup
- [ ] Public pages:
  - [ ] Landing page
  - [ ] Pricing page
  - [ ] Signup form
- [ ] Invitation flow:
  - [ ] Email invitation link
  - [ ] Accept invitation page
  - [ ] Password/MFA setup
- [ ] Organization wizard (step-by-step):
  - [ ] Step 1: Organization name and region
  - [ ] Step 2: Timezone and language
  - [ ] Step 3: SSO configuration (optional)
  - [ ] Step 4: Invite team members
  - [ ] Progress indicator
  - [ ] Form validation with Zod

#### Week 4: Sensor Enrollment
- [ ] Sensor enrollment screen:
  - [ ] Generate one-time enrollment token (API call)
  - [ ] Display install command with copy button
  - [ ] Live status: "Waiting for first data..."
  - [ ] Success confirmation with first health check
- [ ] Guided checklist:
  - [ ] "Getting Started" checklist component
  - [ ] Explain autonomy levels
  - [ ] Link to documentation
- [ ] Place tenant in Monitor-only mode by default
- [ ] Onboarding analytics:
  - [ ] Track time from signup to first data
  - [ ] Track completion rates

**Deliverables:**
- Complete signup to sensor enrollment flow
- Wizard with progress tracking
- First-run checklist

**Acceptance Criteria:**
- New user can sign up and create organization
- Sensor enrollment token generation works
- Install command is correct and copyable
- System detects sensor connection
- Tenant starts in Monitor-only mode

---

## Phase 3: Core Detection Loop (Weeks 5-7)

### Goals
- Alert queue (primary screen)
- Incident detail with explainability
- Feedback mechanism
- Audit logging

### Tasks

#### Week 5: Alert Queue
- [ ] API integration:
  - [ ] Generate OpenAPI client from FastAPI spec
  - [ ] Setup TanStack Query hooks
  - [ ] Mock API for development (MSW)
- [ ] Alert queue table:
  - [ ] TanStack Table with virtualization
  - [ ] Columns: severity, ATT&CK technique, confidence, novelty, source, asset, status, age
  - [ ] Sortable and filterable
  - [ ] Group by incident ID
  - [ ] Pagination (cursor-based)
- [ ] Saved views:
  - [ ] "Needs Action" (default)
  - [ ] "High Severity"
  - [ ] "Unconfirmed"
  - [ ] Custom view creation
- [ ] Bulk actions:
  - [ ] Bulk confirm threat
  - [ ] Bulk mark false positive
  - [ ] Bulk assign

#### Week 6: Incident Detail & Explainability
- [ ] Incident detail page:
  - [ ] URL: `/console/incidents/[id]`
  - [ ] Timeline view of related flows
  - [ ] Involved assets list
  - [ ] Notes and comments section
  - [ ] Assignment controls
- [ ] **Explainability panel** (critical):
  - [ ] Decision display (BLOCK/ALLOW/etc)
  - [ ] Confidence score with visual indicator
  - [ ] Novelty score
  - [ ] Top contributing features (bar chart)
  - [ ] Similar past events
  - [ ] MITRE ATT&CK technique mapping
  - [ ] Recommended action
  - [ ] Model version
  - [ ] Plain-language explanation
- [ ] Action buttons:
  - [ ] Confirm threat
  - [ ] Mark false positive
  - [ ] Request action approval
  - [ ] Escalate
- [ ] Feedback recording:
  - [ ] Send feedback to backend
  - [ ] Show confirmation
  - [ ] Update alert status

#### Week 7: Audit Log & Polish
- [ ] Audit log screen:
  - [ ] Immutable log table
  - [ ] Columns: timestamp, actor (human/AI), action, target, result
  - [ ] Search and filters
  - [ ] Export to CSV
  - [ ] Date range selector
- [ ] Keyboard shortcuts:
  - [ ] `j/k` navigate alerts
  - [ ] `c` confirm threat
  - [ ] `f` false positive
  - [ ] `?` show shortcuts modal
- [ ] Command palette:
  - [ ] Cmd/Ctrl+K to open
  - [ ] Quick navigation
  - [ ] Quick actions
- [ ] Polish:
  - [ ] Loading states
  - [ ] Empty states
  - [ ] Error boundaries
  - [ ] Toast notifications

**Deliverables:**
- Functional alert queue
- Complete incident detail with explainability
- Working feedback loop
- Searchable audit log

**Acceptance Criteria:**
- Analyst can triage 10 alerts in under 2 minutes
- Explainability panel shows all required data
- Feedback is recorded with analyst identity
- Audit log is immutable and searchable
- Keyboard shortcuts work

---

## Phase 4: Governance & Control (Weeks 8-9)

### Goals
- Approval workflow
- Autonomy settings
- Kill switch
- Policy management

### Tasks

#### Week 8: Approvals & Autonomy
- [ ] Approval queue:
  - [ ] List of pending approvals
  - [ ] Columns: action, target, impact preview, confidence, expires at
  - [ ] One-click approve/reject
  - [ ] Re-authentication for destructive actions
  - [ ] Auto-expiry handling
- [ ] Impact preview:
  - [ ] Show number of affected sessions/hosts
  - [ ] Preview network impact
  - [ ] Show risk assessment
- [ ] Autonomy settings screen:
  - [ ] Per-action autonomy level:
    - Monitor Only
    - Recommend
    - Supervised (approval required)
    - Automatic
  - [ ] Global autonomy selector
  - [ ] Action-specific overrides
  - [ ] Confirmation dialog for changes

#### Week 9: Kill Switch & Policy
- [ ] **Kill switch** (critical):
  - [ ] Prominent toggle (red)
  - [ ] Confirmation dialog with re-auth
  - [ ] Forces entire tenant to Monitor-only mode
  - [ ] Persistent banner on all screens when active
  - [ ] Audit log entry
  - [ ] Cannot be undone without confirmation
- [ ] Policy management:
  - [ ] Static rules list
  - [ ] AI-generated rules list
  - [ ] Allowlist management
  - [ ] Maintenance windows
  - [ ] Rule creation form
  - [ ] Rule enable/disable toggle
- [ ] Scheduled maintenance:
  - [ ] Create maintenance window
  - [ ] Auto-suppress alerts during window
  - [ ] Calendar view

**Deliverables:**
- Approval workflow
- Autonomy control
- Working kill switch
- Policy management screens

**Acceptance Criteria:**
- Manager can approve action in under 10 seconds
- Kill switch forces Monitor-only mode immediately
- Persistent banner shows kill switch is active
- Autonomy changes are logged
- Policies can be created and toggled

---

## Phase 5: Operations & Monitoring (Weeks 10-11)

### Goals
- Overview dashboard
- Live feed
- Sensor health monitoring
- Integrations

### Tasks

#### Week 10: Overview & Live Feed
- [ ] Overview dashboard:
  - [ ] Threat level indicator (LOW/MEDIUM/HIGH/CRITICAL)
  - [ ] Alert counts by severity
  - [ ] Items needing action
  - [ ] Sensor health status
  - [ ] Blocked vs flagged counts
  - [ ] Mean time to triage
  - [ ] Charts: Apache ECharts
    - Alert trend (last 7 days)
    - Attack types distribution
    - Top sources
- [ ] Live feed:
  - [ ] WebSocket connection to backend
  - [ ] Real-time alert stream
  - [ ] Pause/resume toggle
  - [ ] Rate indicator (events/sec)
  - [ ] Filters (severity, type)
  - [ ] Backpressure handling
  - [ ] Auto-summarize when rate > threshold
  - [ ] Virtualized list (react-window)

#### Week 11: Sensors & Integrations
- [ ] Sensors screen:
  - [ ] Sensor list table
  - [ ] Columns: name, location, status, version, last check-in
  - [ ] Health indicators (online/degraded/offline)
  - [ ] Model version per sensor
  - [ ] Shadow/canary status
  - [ ] Rollback request button
- [ ] Model management:
  - [ ] Current model version
  - [ ] Rollout status
  - [ ] Canary deployment indicator
  - [ ] Manual rollback trigger
- [ ] Integrations setup:
  - [ ] Webhooks configuration
  - [ ] SIEM integrations (Splunk, QRadar)
  - [ ] Email notifications
  - [ ] Chat notifications (Slack, Teams)
  - [ ] Test connection button

**Deliverables:**
- Overview dashboard with charts
- Real-time live feed
- Sensor health monitoring
- Integration configuration

**Acceptance Criteria:**
- Overview shows accurate stats
- Live feed updates in < 2 seconds
- Sensors status is real-time
- Integrations can be configured and tested
- WebSocket reconnects automatically

---

## Phase 6: Commercial & Compliance (Week 12)

### Goals
- Reporting and compliance
- Billing integration
- Settings and administration
- Trust center

### Tasks

#### Week 12: Reports, Billing, Settings
- [ ] Reports screen:
  - [ ] Report templates: PCI DSS, ISO 27001, NBE compliance
  - [ ] Date range selector
  - [ ] Generate report (async job)
  - [ ] Download PDF/CSV
  - [ ] Scheduled reports
  - [ ] Email delivery
- [ ] Billing screen:
  - [ ] Current plan display
  - [ ] Usage metering visualization
  - [ ] Invoice list
  - [ ] Stripe Customer Portal integration
  - [ ] Payment method management
  - [ ] Invoice payment for enterprise
- [ ] Settings:
  - [ ] User management (list, invite, remove)
  - [ ] Role assignment
  - [ ] SSO configuration (SAML/OIDC)
  - [ ] SCIM provisioning setup
  - [ ] API keys management
  - [ ] Notification preferences
  - [ ] Data region display (read-only)
- [ ] Trust center (public):
  - [ ] Security practices
  - [ ] Compliance certifications
  - [ ] Privacy policy
  - [ ] Terms of service
  - [ ] Status page link

**Deliverables:**
- Compliance report generation
- Billing integration
- Full settings screen
- Trust center pages

**Acceptance Criteria:**
- Reports generate correctly
- Billing shows accurate usage
- SSO can be configured
- API keys can be created and revoked
- Trust center is accessible

---

## Phase 7: Operator Console (Week 13-14)

**Note:** Separate application from tenant console

### Goals
- Tenant fleet management
- Support access with audit trail
- Model rollout controls
- Usage and revenue dashboard

### Tasks

#### Week 13-14: Operator App
- [ ] Separate Next.js project:
  ```
  operator-console/
    app/
      tenants/
      sensors/
      models/
      support/
      revenue/
  ```
- [ ] Tenant management:
  - [ ] Tenant list with health indicators
  - [ ] Tenant detail (usage, alerts, sensors)
  - [ ] Tenant creation/suspension
  - [ ] Feature flag per tenant
- [ ] Support access:
  - [ ] Time-limited impersonation
  - [ ] Requires tenant consent
  - [ ] Visible banner to support user
  - [ ] Logged in tenant audit log
  - [ ] Automatic expiry (4 hours max)
- [ ] Model rollout:
  - [ ] Fleet-wide model version view
  - [ ] Per-tenant rollout control
  - [ ] Canary deployment (% of tenants)
  - [ ] Rollback button
  - [ ] Deployment health metrics
- [ ] Revenue dashboard:
  - [ ] MRR, ARR
  - [ ] Usage by tenant
  - [ ] Churn indicators
  - [ ] Plan distribution

**Deliverables:**
- Operator console app
- Tenant management
- Support access with audit
- Model rollout controls

**Acceptance Criteria:**
- Operator can view all tenants
- Support access is time-limited and logged
- Models can be rolled out gradually
- Revenue metrics are accurate

---

## Phase 8: Advanced Features (Week 15+)

**Post-MVP enhancements**

### Planned Features
1. **AI Investigation Copilot**
   - Natural language queries
   - Automated investigation steps
   - Approval gates for actions

2. **Attack Path Visualization**
   - Network graph (Cytoscape.js or Sigma.js)
   - Lateral movement tracking
   - ATT&CK stage overlays
   - Interactive exploration

3. **Detection-as-Code**
   - Custom detection rules in YAML
   - Simulation against historical traffic
   - Version control integration
   - What-if analysis

4. **Case Management**
   - Ticket creation and tracking
   - Shift handoff notes
   - Case collaboration
   - SLA tracking

5. **Mobile Companion App**
   - Push notifications
   - Approve actions on mobile
   - Alert overview
   - iOS and Android

6. **Advanced Analytics**
   - Predictive threat modeling
   - Anomaly trends
   - Effectiveness scoring
   - ROI calculator

---

## Cross-Cutting Requirements (Ongoing)

### Security (Every Phase)
- [ ] CSP with no unsafe-inline
- [ ] Input sanitization (traffic data is hostile)
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Re-auth for sensitive actions
- [ ] Idle session timeout
- [ ] Dependency scanning (weekly)
- [ ] Security headers (HSTS, X-Content-Type-Options, etc)

### Testing (Every Phase)
- [ ] Unit tests (Vitest) for logic
- [ ] Component tests (React Testing Library)
- [ ] E2E tests (Playwright) for critical flows
- [ ] Tenant isolation tests (dedicated suite)
- [ ] Accessibility tests (automated + manual)
- [ ] Performance tests (Lighthouse CI)

### Accessibility (Every Phase)
- [ ] WCAG 2.2 AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader labels
- [ ] Sufficient contrast (both themes)
- [ ] Focus indicators
- [ ] No color-only information

### Performance (Every Phase)
- [ ] Alert queue < 2s first render
- [ ] Interaction latency < 200ms
- [ ] Live feed latency < 2s
- [ ] JS bundle budget enforced
- [ ] Lazy loading for routes
- [ ] Image optimization

### Observability (Every Phase)
- [ ] OpenTelemetry instrumentation
- [ ] Sentry error tracking
- [ ] Performance monitoring
- [ ] User session replay (opt-in)
- [ ] Tenant-safe data scrubbing

---

## Success Metrics

### MVP Success (End of Phase 4)
- Time from signup to first data < 5 minutes
- Alert triage time < 1 minute per incident
- Kill switch activation < 5 seconds
- Zero cross-tenant data leakage
- WCAG 2.2 AA compliance

### Production Success (End of Phase 6)
- Console uptime 99.9%
- Alert to screen latency < 2 seconds
- Report generation < 30 seconds
- Mobile-responsive (bonus)
- English + Amharic support (future)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Scope creep | Phase-gated development, MVP first |
| Performance degradation | Budget enforcement, Lighthouse CI |
| Security vulnerability | Weekly scans, penetration test before GA |
| Tenant data leakage | Mandatory isolation tests, security review |
| Poor UX causing alert fatigue | User testing after Phase 3, feedback loops |
| Over-promising AI capability | Honest confidence display, explanation panel |

---

## Development Principles

1. **Security First:** Every feature reviewed for security implications
2. **Tenant Isolation:** Zero tolerance for cross-tenant leakage
3. **Explainability:** Every AI decision has a reason
4. **Progressive Enhancement:** Core works without JS (where possible)
5. **Accessibility:** WCAG 2.2 AA from day one
6. **Performance:** Monitor bundle size, enforce budgets
7. **Testing:** No feature without tests
8. **Documentation:** Code is documented, Storybook updated

---

## Current Status & Next Steps

**Completed:**
- [x] Phase 1: Basic Next.js structure created
- [x] Tailwind CSS installed
- [x] Dashboard packages installed (recharts, socket.io-client, @tanstack/react-query, zustand)

**Immediate Next Steps (This Week):**
1. Complete Phase 1: Foundation
   - Install remaining dependencies (shadcn/ui, React Hook Form, Zod)
   - Setup project folder structure
   - Configure authentication (choose provider)
   - Implement multi-tenant routing

2. Begin Phase 2: Onboarding
   - Design organization wizard
   - Create signup flow mockups

**Blocker:** Training must complete before backend integration in Phase 3.

---

## Timeline Summary

| Phase | Weeks | Deliverable |
|-------|-------|-------------|
| 1. Foundation | 1-2 | Auth, routing, design system |
| 2. Onboarding | 3-4 | Signup, wizard, sensor enrollment |
| 3. Core Loop | 5-7 | Alert queue, explainability, audit log |
| 4. Governance | 8-9 | Approvals, kill switch, policy |
| **MVP READY** | **Week 9** | **First pilot possible** |
| 5. Operations | 10-11 | Dashboard, live feed, integrations |
| 6. Commercial | 12 | Billing, reports, compliance |
| 7. Operator Console | 13-14 | Fleet management, support access |
| 8. Advanced | 15+ | Copilot, graph viz, case mgmt |

**First production-ready release:** End of Week 12  
**Full enterprise features:** End of Week 14

---

## Questions for Product/Stakeholders

1. **Hosting:** Single cloud region first, or Ethiopia-based region from start?
2. **Identity:** Managed provider (Auth0) for speed, or self-hosted Keycloak for data residency?
3. **Amharic:** Include in first release, or English-only MVP?
4. **Branding:** White-labeled subdomains per customer, or single branded console?
5. **Mobile:** Priority for Phase 8, or defer?
6. **Payment:** Card-only initially, or invoice/PO support from start?

---

**Document Status:** Living roadmap, updated weekly  
**Last Updated:** October 24, 2026  
**Owner:** Development Team  
**Stakeholders:** Product, Security, Compliance
