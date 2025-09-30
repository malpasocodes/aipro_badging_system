# UI/UX Specification
**Badging System — Streamlit App**  
**Stack:** Python • Streamlit • uv • Render  
**Doc Version:** 1.0 • **Date:** 2025-09-28

---

## 1) Purpose & Scope
This document defines information architecture, user journeys, screens, components, interaction patterns, content style, accessibility, and visual tokens for the Badging System. It targets v1 (MVP) while remaining extensible.

---

## 2) Primary Personas
- **Student**: Earns badges (Program → Skill → Mini-badge → Capstone), views progress, receives decisions.
- **Assistant**: Approves/rejects requests, manages roster; cannot delete accounts or retire badges.
- **Administrator**: All Assistant abilities + manages programs/skills/mini-badges, exports, settings.

---

## 3) Core Journeys
### J1: Sign-in & Onboarding (All)
1. Google Sign-In → email verified.  
2. Onboarding form: Substack email, Meetup email, username (policy), acknowledgement of privacy.  
3. Confirmation screen with next-step CTA: “Go to Dashboard”.

### J2: Student Earns a Mini-badge
1. Browse Program → Skill → Mini-badge detail.  
2. Click **Request Credit** (v1 assumes no evidence upload).  
3. Review request summary → Submit.  
4. See request in **My Requests** with status (Pending / Approved / Rejected).

### J3: Assistant/Administrator Approval
1. **Approvals Queue** → filter by Program/Skill/Status.  
2. Open request → view student info (redacted where required), history, policy hints.  
3. **Approve** or **Reject** with reason → instant toast + status chip update.  
4. Auto-notification sent to student; audit entry created.

### J4: Administrator Maintains Catalog & Exports
1. **Admin → Catalog**: create/edit Program/Skill/Mini-badge/Capstone.  
2. **Admin → Exports**: select dataset → confirm PII redaction preview → export CSV.  
3. Export success toast; audit entry logged.

---

## 4) Information Architecture & Navigation
- **Global Nav (Streamlit sidebar)**  
  - Home (role-aware overview)  
  - **Badges**
    - Catalog (browse Programs → Skills → Mini-badges)  
    - My Progress (Student)  
  - **Approvals** (Assistant, Admin)  
  - **Admin** (Admin only)
    - Catalog Management
    - Roster
    - Exports
    - Settings
  - Profile & Help

- **Top Bar (main content header area)**  
  - Page title, context breadcrumbs (e.g., Badges › Program › Skill)  
  - Status chips, action buttons (role-aware)

---

## 5) Screens & States
### S1: Sign-In
- **Components**: Google Sign-In button, brief privacy note, support link.
- **States**: Loading (spinner), Error (OAuth failed / retry), Signed-out.

### S2: Onboarding
- **Fields**: Substack email, Meetup email, username, consent checkbox.  
- **Validation**: email format; username policy; required consent.  
- **Actions**: Submit, Save Draft (optional), Cancel.  
- **States**: Inline errors, disabled submit until valid, success confirmation.

### S3: Home Dashboard (role-aware)
- **Student**: “Start Earning” quick links, My Progress summary (cards), recent decisions.  
- **Assistant**: Approvals at a glance (counts, quick filters), recent actions.  
- **Admin**: System overview (counts, last export, audit alerts), catalog shortcuts.

### S4: Catalog (Browse)
- **Layout**: Left column filter (Program/Skill), main grid of cards.
- **Card**: Title, description, counts (skills/mini badges), CTA.  
- **Empty**: “No Programs yet” (Admin CTA to create).  
- **Loading**: skeleton cards.

### S5: Skill / Mini-badge Detail
- **Panels**: Overview, Requirements, Progress, History.  
- **Actions**: Request Credit (Student), Edit (Admin), View Requests (Assistant/Admin).  
- **States**: Requirement chips (complete/incomplete), status timeline.

### S6: My Progress (Student)
- **Visual**: Progress bars by Program and Skill.  
- **Table**: Mini-badges with status, last action, next step.  
- **Filters**: Program, Status (All/Pending/Approved/Rejected).

### S7: Approvals Queue (Assistant/Admin)
- **Controls**: Search by user/mini-badge; filters: Program, Skill, Status.  
- **Table columns**: Request ID, Student, Program/Skill/Mini-badge, Submitted, Status, Actions.  
- **Row actions**: View, Approve, Reject. Bulk Approve (optional in v1).  
- **Empty**: “No pending requests.”

### S8: Request Detail (Assistant/Admin)
- **Header**: Student (masked email if redaction required), Badge path, Submission time.  
- **Tabs**: Summary, History (audit), Policy.  
- **Primary actions**: Approve / Reject + reason (modal).  
- **Side info**: related requests, student progress context.

### S9: Admin → Catalog Management
- **CRUD**: Program, Skill, Mini-badge, Capstone.  
- **Form**: title, description, prerequisites (mini-badge list), active toggle.  
- **Validation**: cyclic dependency guard, uniqueness.  
- **States**: create/edit/delete confirmations.

### S10: Admin → Roster
- **Table**: User, Role, Joined, Last Active, Actions (change role, deactivate).  
- **Safety**: Cannot delete accounts (policy), confirm role change.  
- **Bulk**: CSV import (future).

### S11: Admin → Exports
- **Picker**: Dataset type (Awards, Requests, Catalog, Roster).  
- **Preview**: Sample rows with **PII columns visibly stricken/omitted**.  
- **Toggle**: “Include PII” (disabled in v1).  
- **Action**: Export CSV → success toast with audit link.

### S12: Profile
- **View**: Google account (read-only), Substack/Meetup emails, username.  
- **Actions**: Update onboarding fields, sign out.

---

## 6) Component Library (Streamlit Mappings)
- **Buttons**: primary/secondary/danger (`st.button`, `st.download_button`)
- **Inputs**: text, email, select/radio, multiselect, date, checkbox.  
- **Chips/Badges**: status via colored `st.markdown` + emoji or custom HTML (within safety).  
- **Tables**: `st.dataframe` for interactive, `st.table` for static summaries.  
- **Cards**: container + bordered style using `st.container` + CSS.  
- **Tabs**: `st.tabs(["Summary","History","Policy"])`  
- **Toasts**: `st.toast()` (or temporary `st.success`/`st.error`).  
- **Modals**: emulate with `st.modal` (if available) or conditional containers.  
- **Loaders**: `st.spinner("Loading...")` + skeleton placeholders.  
- **Icons**: emoji or small SVG (Streamlit-safe).

---

## 7) Interaction Patterns & States
- **Loading**: spinner + skeletons for lists/cards; avoid blocking entire page when possible.
- **Empty**: Explain why empty and provide next action (e.g., “Create Program”).  
- **Error**: Friendly message + “Try again” + error code for support.  
- **Success**: unobtrusive toast + in-place update (optimistic UI where safe).  
- **Confirmation**: destructive/binding actions require confirm step (role change, delete catalog item).  
- **Undo**: Provide undo for non-destructive ops where feasible (e.g., clear filters).

---

## 8) Forms & Validation
- **Inline validation**: live checks for email format, username policy.  
- **Disabled submit** until required fields valid.  
- **Error messages**: short, actionable (“Enter a valid email like name@example.com”).  
- **Autosave (optional)**: preserve draft inputs on navigation.  
- **Keyboard**: Enter submits forms where unambiguous.

---

## 9) Notifications
- **In-app**: toasts for actions; notification center (simple list) for decisions.  
- **Email (future)**: template microcopy and link to request detail.  
- **Status chips**: Pending (grey), Approved (green), Rejected (red).

---

## 10) Accessibility (A11y)
- High color-contrast tokens; never convey status by color alone (use icons/labels).  
- All interactive elements keyboard reachable; visible focus states.  
- Form labels and helper text; error associations (`aria-*` where possible).  
- Motion: minimal; avoid auto-refresh that steals focus.  
- Alt text for any images; descriptive link text (avoid “click here”).

---

## 11) Privacy & PII Redaction UX
- **PII badges** next to fields that are sensitive.  
- **Redaction preview** before export; show masked emails (e.g., `al***@example.com`).  
- **Tooltips** explaining why data is masked and who can see it.  
- **Audit banners** on pages with export/approval actions.

---

## 12) Visual Design Tokens (Streamlit-friendly)
- **Typography**: System default; headings use `st.markdown("## …")`.  
- **Spacing**: 8px scale (4/8/16/24/32).  
- **Color (semantic)**: Primary, Success, Warning, Danger, Neutral.  
- **Elevation**: cards with subtle border + shadow via CSS.  
- **Density**: Comfortable by default; compact tables for queues.

---

## 13) Responsive Behavior
- **Mobile**: single-column flow; actions stacked; sticky Approve/Reject at bottom.  
- **Tablet/Desktop**: two-column layouts for detail + side context.  
- **Tables**: horizontal scroll on small screens; allow column hide.

---

## 14) Content Style & Microcopy
- **Tone**: clear, neutral, supportive.  
- **Buttons**: verb-first (“Request Credit”, “Approve”, “Export CSV”).  
- **Errors**: say what happened and what to do next.  
- **Empty states**: suggest a next step.  
- **Examples**:  
  - Toast (success): “Mini-badge approved. The student has been notified.”  
  - Toast (error): “Couldn’t load approvals. Check your connection and try again.”  
  - Help text: “Your Substack email helps us link your subscription.”

---

## 15) Telemetry (Privacy-Preserving)
- Events: sign-in success/fail, onboarding completed, request submitted, approval actioned, export generated.  
- Use aggregate counts; avoid storing PII in event payloads.  
- Surface key metrics on Admin Home.

---

## 16) UX Acceptance Criteria (MVP)
- A user can sign in with Google and complete onboarding in ≤ 2 minutes.  
- A student can request a mini-badge credit in ≤ 3 clicks from the mini-badge detail page.  
- An assistant can approve/reject from the queue without leaving the page.  
- Admin can create Program/Skill/Mini-badge and see it appear in Catalog immediately.  
- Export flow always shows a redaction preview before enabling download.

---

## 17) Streamlit Routing & Layout Guidance
- Use `st.sidebar` for global nav; main pane for content.
- Wrap pages in a simple router (query params or `st.session_state["route"]`).  
- Persist filters in `st.session_state`.  
- Defer heavy queries until filters chosen; show skeletons.

---

## 18) Future Enhancements (Post-v1)
- Evidence upload and rubric display.  
- Bulk approvals and CSV roster import.  
- Email notifications with templating.  
- Badges as verifiable credentials (Open Badges).

---

**End of UI/UX Specification**