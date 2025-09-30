# Product Requirements Document (PRD)  
**AIPPRO Badging System**  

---

## 1. Overview  
The Badging System will provide a structured way to recognize and track student achievement through digital badges. Built with **Python + Streamlit**, managed with **uv (venv + package management)**, and deployed on **Render**, the system will support identity verification, onboarding, role-based approvals, and progression from mini-badges to capstones.  

---

## 2. Goals & Objectives  
- Provide a secure, simple sign-in using **Google Sign-In** with email verification.  
- Require onboarding with **Substack** and **Meetup** subscription emails.  
- Enable structured badge progression: **Program → Skills → Mini-badges → Capstone**.  
- Allow Administrators and Assistants to approve badge requests with clear permissions.  
- Support notifications for approvals/rejections.  
- Ensure compliance with **PII redaction** and retention policies.  
- Provide export features for Administrators only.  

---

## 3. Scope (v1)  
### In-Scope  
- Google-only authentication with email verification.  
- Onboarding form for verification (Substack + Meetup emails).  
- Roles: **Administrator**, **Assistant**, **Student**.  
- Badge structure and awarding flow.  
- Approval workflow (Admin + Assistant).  
- Notifications (approve/reject).  
- Roster management for Admin + Assistant.  
- Admin exports.  
- PII redaction in exports and audit logs.  

### Out-of-Scope (v1)  
- Evidence storage.  
- Badge expiration.  
- External API integrations beyond Google/Render.  
- Mobile app.  

---

## 4. User Roles & Permissions  
- **Administrator**: Full control (approve/reject, exports, roster, badge management, retire badges).  
- **Assistant**: Approve/reject, manage roster; **cannot create, delete accounts or retire badges**.  
- **Student**: View badges, request/earn badges, view notifications.  

---

## 5. Workflows  
### Identity & Onboarding  
1. User signs in with Google.  
2. System verifies email.  
3. User completes a form  for onboarding, including their substack and meetup emails.
4. Admin/Assistant validates onboarding info.  

### Badge Progression  
- Students earn **mini-badges** under each Skill.  
- Completion of all mini-badges in a Skill → Skill Badge.  
- Completion of all Skills in a Program → Full Badge.  
- Some Programs include a **Capstone** requirement.  

### Approval & Notifications  
- Badge requests routed to **Admin/Assistant**.  
- Approvals/denials logged with audit trail.  
- Notifications sent to Student.  

---

## 6. Policies  
- **No domain restriction** on sign-in.  
- **No evidence storage** for v1.  
- **No expiry** on badges.  
- **PII redaction** enforced for all exports.  
- **Retention policy**: Audit logs retained, but exports stripped of sensitive data.  

---

## 7. Success Metrics  
- Avg. time from badge request to decision < **48 hrs**.  
- > **95%** successful onboarding (email verified + Substack/Meetup provided).  
- > **90%** uptime SLA on Render deployment.  
- Export compliance checks show **0 PII violations**.  

---

## 8. Risks & Mitigations  
- **Risk**: Email verification bypass → **Mitigation**: enforce Google OAuth + server-side verification.  
- **Risk**: PII leakage in exports → **Mitigation**: redaction + testing.  
- **Risk**: Deployment instability → **Mitigation**: CI/CD pipeline with rollback on Render.  

---

## 9. Timeline (linked to Project Plan)  
10 phases: setup, auth, onboarding, RBAC, badge model, earning flow, notifications, exports, UX polish, deployment.  

---

## 10. Dependencies  
- **Python 3.11+**  
- **Streamlit** (UI framework)  
- **uv** (package management + venv)  
- **Render** (deployment)  
- **Google Identity Services** (OAuth)  

---

**Version:** 1.0  
**Author:** Alfred Essa  
**Date:** 2025-09-29