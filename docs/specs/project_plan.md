# Project Plan
**Badging System**  
**Stack:** Python • Streamlit • uv • Render • Google Identity Services  
**Doc Version:** 1.0 • **Date:** 2025-09-27

---

## Overview
This project plan defines 10 incremental phases for designing, implementing, testing, and deploying the Badging System. Each phase lists goals, deliverables, acceptance criteria, and risks.

---

## Phase 1: Project Setup & Repo Initialization
**Goal:** Establish project scaffolding and development workflow.  
**Deliverables:**
- GitHub repo created with branching strategy.
- `uv` environment and lockfile (`uv.lock`).
- Base `pyproject.toml` with dependencies.  
- CI (lint, type check, tests).  
**Acceptance Criteria:** CI passes on empty skeleton.  
**Risks:** Misconfigured CI → mitigated by sample workflow.

---

## Phase 2: Authentication & Session Management
**Goal:** Implement Google Sign-In with email verification.  
**Deliverables:**
- OAuth2 via Google Identity Services.  
- Session management (signed cookies / Streamlit session state).  
- Basic user table integration.  
**Acceptance Criteria:** User can sign in/out and be recognized by role.  
**Risks:** OAuth integration complexity.

---

## Phase 3: Onboarding Flow
**Goal:** Capture Substack + Meetup emails at first login.  
**Deliverables:**
- Onboarding form with validation.  
- Store onboarding info in `users` table.  
- Consent checkbox and policy notice.  
**Acceptance Criteria:** New user completes onboarding in ≤ 2 minutes.  
**Risks:** Incorrect validation → mitigated with regex + test cases.

---

## Phase 4: Roles & Approvals Queue
**Goal:** Implement RBAC and approval workflows.  
**Deliverables:**
- Role assignment (admin, assistant, student).  
- Approvals queue for pending badge requests.  
- Approve/reject actions with reason.  
- Audit logs for decisions.  
**Acceptance Criteria:** Assistant can approve/reject; admin can also.  
**Risks:** Role leakage → enforce with server-side checks.

---

## Phase 5: Badge Data Model & Catalog
**Goal:** Define Programs, Skills, Mini-badges, Capstones.  
**Deliverables:**
- DB schema + CRUD for catalog.  
- Admin UI for managing catalog.  
- Student browse view.  
**Acceptance Criteria:** Admin can create Program → Skill → Mini-badge and student can browse.  
**Risks:** Complex DAG rules → validate on creation.

---

## Phase 6: Earning Logic & Awards
**Goal:** Enable students to request and earn badges.  
**Deliverables:**
- Request submission flow.  
- Automatic award granting for Skills/Programs when requirements met.  
- My Progress view with progress bars.  
**Acceptance Criteria:** Completing all mini-badges → Skill award; all skills → Program award.  
**Risks:** Logic errors → add integration tests.

---

## Phase 7: Notifications & Audit Trails
**Goal:** Provide visibility of actions and outcomes.  
**Deliverables:**
- Notification service for in-app messages.  
- Notification center UI.  
- Complete audit log table.  
**Acceptance Criteria:** Student receives notification on decision; admin sees audit entries.  
**Risks:** Over-notification → add deduplication.

---

## Phase 8: Exports & PII Redaction
**Goal:** Allow admins to export compliance-ready data.  
**Deliverables:**
- Export service with PII-stripping.  
- Admin export UI with preview.  
- CSV download feature.  
**Acceptance Criteria:** Admin exports contain no PII.  
**Risks:** Data leakage → enforced test suite for exports.

---

## Phase 9: UX Polish & Accessibility
**Goal:** Improve usability and accessibility.  
**Deliverables:**
- Streamlit UI refinements (cards, tables, progress).  
- Responsive design testing.  
- A11y pass (color contrast, keyboard nav).  
**Acceptance Criteria:** Users complete flows quickly; meets WCAG AA basics.  
**Risks:** Streamlit limitations → workarounds with CSS.

---

## Phase 10: Deployment & Launch
**Goal:** Deploy to Render with monitoring and go-live readiness.  
**Deliverables:**
- Render service setup (Web + Postgres).  
- Env vars configured securely.  
- Health checks and monitoring.  
- Backup/restore tested.  
**Acceptance Criteria:** Site live at custom domain, uptime > 90% SLA.  
**Risks:** Cold-start latency → mitigated with pre-warm.

---

## Cut Criteria for v1
- Authentication + Onboarding.  
- RBAC + Approvals queue.  
- Badge data model + earning flow.  
- Notifications + exports.  
- Render deployment stable.

## Backlog for v1.1
- Evidence upload.  
- Email notifications.  
- Bulk approvals.  
- Open Badges compliance.

---

**End of Project Plan**
