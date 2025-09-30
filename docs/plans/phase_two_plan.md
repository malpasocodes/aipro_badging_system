# Phase Two Plan: Authentication & Session Management (Restructured)

**Project:** AIPPRO Badging System  
**Phase:** 2 of 10 (Split into 2A, 2B, 2C)  
**Created:** 2025-09-30  
**Revised:** 2025-09-30  
**Status:** Pending Approval

---

## Overview & Restructuring Rationale

**Original Challenge:** The initial Phase 2 plan was overly ambitious, attempting to implement full OAuth, session management, RBAC, and database integration in a single phase.

**Revised Approach:** Split into three manageable sub-phases to de-risk authentication in Streamlit and maintain development momentum.

---

## Phase 2A: Sign-in + Minimal User Record (Must-have)

### Objectives
Establish basic Google sign-in functionality with minimal user record storage. Focus on getting users authenticated with the simplest secure approach.

**Primary Goals:**
- Implement Google Identity Services "Sign in with Google" button
- Server-side ID token verification (audience, issuer, expiry)
- Create minimal users table with single migration
- Bootstrap admin via environment variable allowlist
- Simple session state management

### Technical Approach (Phase 2A)
1. **Authentication Method**: OIDC ID token verification (simpler than full OAuth code flow)
2. **Database**: Single users table migration with basic fields
3. **Session**: Stateless approach using st.session_state (re-verify token on each load)
4. **Admin Bootstrap**: Environment variable ADMIN_EMAILS for admin designation
5. **CI Strategy**: Mock Google ID token verifier for testing

### Deliverables (Phase 2A)
- [x] Mock Google authentication system (Phase 2A implementation)
- [x] Server-side ID token verification framework (with MockAuthService)
- [x] Basic users table with Alembic migration
- [x] Admin bootstrap via ADMIN_EMAILS environment variable
- [x] Authentication state management in st.session_state with timeout
- [x] User interface with email display and sign-out functionality
- [x] MockAuthService for CI testing (15/15 tests passing)
- [x] Comprehensive error handling for authentication failures

### Acceptance Criteria (Phase 2A)
1. ✅ **Valid ID Token**: User signs in, record created/loaded, shows "Signed in as X"
2. ✅ **Invalid Token**: User stays signed out with friendly error message
3. ✅ **Admin Recognition**: Email in ADMIN_EMAILS gets admin role, others get student
4. ✅ **Protected Routes**: Visiting protected page while signed out shows sign-in prompt
5. ✅ **CI Testing**: Tests run with mocked verifier, no live Google API calls

### Phase 2A Completion Status
**Status:** ✅ COMPLETED  
**Date:** September 29, 2025  
**Implementation:** Mock authentication system fully functional with comprehensive testing  
**Outcome Log:** See `docs/logs/phase_two_a_outcome.md` for detailed completion report  

---

## Phase 2B: Durable Session + RBAC Guards (Should-have)

### Objectives
Add session persistence across page refreshes and implement role-based access control guards.

**Primary Goals:**
- Server-signed session tokens with secure storage
- Session persistence across browser refreshes
- Role-based route protection decorators
- Enhanced session security with rotation

### Technical Approach (Phase 2B)
1. **Session Tokens**: Use itsdangerous for server-signed session tokens
2. **Storage**: Store session token in st.session_state with persistence
3. **RBAC**: Implement require_role(*roles) decorator
4. **Security**: SameSite protection, expiration checks, session rotation

### Deliverables (Phase 2B)
- [ ] Server-signed session token implementation
- [ ] Session persistence across page loads
- [ ] require_role(*roles) decorator for route protection
- [ ] Page-level access control guards
- [ ] Session rotation on re-authentication
- [ ] Enhanced error handling and user feedback
- [ ] Unit tests for RBAC functionality

### Acceptance Criteria (Phase 2B)
1. **Session Persistence**: Authentication state survives page refresh
2. **Route Protection**: Unauthorized users cannot access protected pages
3. **Role Enforcement**: Admin/assistant/student access properly differentiated
4. **Security**: Session tokens properly signed and validated
5. **Testing**: Unit tests cover all RBAC scenarios

---

## Phase 2C: OAuth Code + PKCE (Optional/Future)

### Objectives
Implement full OAuth authorization code flow with PKCE for future Google API access needs.

**Primary Goals:**
- Full OAuth 2.0 authorization code flow
- PKCE (Proof Key for Code Exchange) implementation
- Server-side callback handler
- Token exchange and storage

### Technical Approach (Phase 2C)
1. **OAuth Flow**: Full authorization code flow with PKCE
2. **Callback Handler**: FastAPI sidecar or Streamlit experimental routing
3. **Security**: Server-side token exchange, never expose tokens to client
4. **Integration**: Maintain compatibility with 2A/2B implementations

### Deliverables (Phase 2C)
- [ ] OAuth authorization code flow with PKCE
- [ ] Callback endpoint handler (/oauth/callback)
- [ ] Server-side code-to-token exchange
- [ ] Access token storage for future API calls
- [ ] Regression tests for all auth flows
- [ ] Migration path from 2B implementation

### Acceptance Criteria (Phase 2C)
1. **OAuth Flow**: Complete PKCE flow functions correctly
2. **Security**: Tokens never exposed to client-side code
3. **Compatibility**: All Phase 2A/2B functionality maintained
4. **Testing**: Comprehensive test coverage for OAuth flows
5. **API Ready**: Foundation for future Google API integrations

## Implementation Strategy

### Phase Priority
1. **Phase 2A (Must-have)**: Critical for basic user authentication
2. **Phase 2B (Should-have)**: Required for production-ready session management
3. **Phase 2C (Optional)**: Only implement if future Google API access needed

### Key Simplifications in 2A
- **Authentication**: OIDC ID token verification instead of full OAuth flow
- **Session**: Stateless with st.session_state instead of complex cookie management
- **Database**: Single migration, minimal schema, no connection pooling
- **Admin**: Simple environment variable allowlist instead of complex role system
- **Testing**: Mock verifier approach to avoid live Google API dependency

### Progression Path
- Start with 2A for immediate user sign-in capability
- Add 2B when session persistence becomes critical
- Consider 2C only if server-side Google API access is required

## Technical Implementation Details

### Database Schema (Phase 2A)
```sql
-- Minimal users table for Phase 2A
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_sub VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student' 
        CHECK (role IN ('admin', 'assistant', 'student')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Basic indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_sub ON users(google_sub);
```

### ID Token Verification (Phase 2A)
```python
def verify_google_id_token(id_token: str) -> dict:
    """Verify Google ID token and return user claims."""
    # Verify issuer, audience, expiry, email_verified
    # Return claims: sub, email, name, picture
```

### Environment Configuration (Phase 2A)
```bash
# Required for Phase 2A
GOOGLE_CLIENT_ID="your_google_client_id"
ADMIN_EMAILS="admin@example.com,admin2@example.com"
DATABASE_URL="postgresql://..."

# Future phases
APP_SECRET_KEY="for_signed_sessions_in_2B"
```

## Risks and Mitigation Strategies

### Phase 2A Specific Risks
1. **Google API Changes**: ID token format or verification requirements change
   - **Mitigation**: Use official Google libraries, monitor deprecation notices
   - **Contingency**: Mock verifier allows development to continue

2. **Database Migration Issues**: First real database integration
   - **Mitigation**: Simple schema, thorough testing, backup procedures
   - **Contingency**: Database reset procedures for development

3. **Streamlit Session Limitations**: Session state behavior changes
   - **Mitigation**: Minimal dependency on session state, clear documentation
   - **Contingency**: Alternative storage mechanisms in Phase 2B

### General Risks (All Phases)
1. **Environment Configuration**: Missing or incorrect OAuth credentials
   - **Mitigation**: Clear setup documentation, validation on startup
   - **Contingency**: Development mode with mock authentication

2. **Testing Complexity**: Mocking Google services effectively
   - **Mitigation**: Simple mock strategy, focus on business logic testing
   - **Contingency**: Manual testing procedures documented

## Timeline & Dependencies

### Phase 2A Timeline
**Duration**: 1-2 days
- Day 1: Database setup, user table migration, basic Google integration
- Day 2: ID token verification, admin bootstrap, testing, UI integration

### Phase 2B Timeline (Future)
**Duration**: 1-2 days  
- Day 1: Session token implementation, persistence
- Day 2: RBAC decorators, route protection, testing

### Phase 2C Timeline (Optional)
**Duration**: 1-2 days
- Day 1: OAuth flow setup, callback handler
- Day 2: Integration testing, migration from 2B

### Dependencies (Phase 2A)
- Phase 1 completion (project structure, tooling)
- Google Cloud Console project with OAuth client configured
- PostgreSQL database access (local or Render)
- Environment variables configured

## Success Metrics (Phase 2A)

### Concrete Acceptance Tests
1. **Valid Google ID Token**: 
   - App shows "Signed in as [email]"
   - User record created/loaded in database
   - Admin emails get admin role, others get student role

2. **Invalid/Expired Token**:
   - User stays signed out
   - Friendly error message displayed
   - No database record created

3. **Protected Route Access**:
   - Signed-out user visiting protected page sees sign-in prompt
   - Error message: "Please sign in to access this page"

4. **CI Testing**:
   - Tests run with mocked Google verifier
   - No outbound calls to live Google APIs
   - All authentication scenarios covered

### Performance Targets (Phase 2A)
- **Sign-in Time**: Complete ID token verification in < 1 second
- **Database Query**: User lookup/creation in < 200ms
- **Page Load**: Authenticated state check in < 100ms

---

## Integration with Future Phases

### Phase 3 (Onboarding) Setup
- User table ready for onboarding fields (username, substack_email, meetup_email)
- Authentication state supports onboarding flow detection
- New user redirect mechanism prepared

### Phase 4 (RBAC) Foundation
- Basic role assignment (admin/assistant/student) implemented
- Role checking patterns established
- Admin bootstrap mechanism ready for expansion

### Long-term Architecture
- Database layer ready for additional tables
- Authentication patterns ready for RBAC expansion
- Security patterns established for audit logging

## Recommended Approach

### Start with Phase 2A Only
- Focus on getting basic sign-in working first
- Validate the Google integration and database setup
- Establish testing patterns and CI integration
- Provides immediate user value and reduces risk

### Decision Points
- **After 2A**: Evaluate if session persistence is needed immediately
- **Before 2B**: Determine if the simple st.session_state approach is sufficient
- **Before 2C**: Assess if server-side Google API access is required

### Success Criteria for Moving to Next Phase
- **Phase 2A → 2B**: Session state not persisting properly or UX issues
- **Phase 2B → 2C**: Need for server-side Google API calls (Drive, Calendar, etc.)
- **Phase 2A → Phase 3**: Basic auth working, ready for onboarding flow

---

## Next Steps After Phase 2A Completion

Upon successful completion and acceptance of Phase 2A:
1. Users can authenticate with Google ID tokens
2. Basic user records are created and maintained
3. Admin users are properly identified
4. Foundation is ready for onboarding flow (Phase 3)
5. Decision made on whether Phase 2B is needed immediately

---

## APPROVAL

**Status:** Approved  
**Reviewed by:** Alfred Essa  
**Date:** 2025-09-30 22:30 UTC  
**Notes:** Approved to proceed with Phase 2A implementation. Restructured approach addresses complexity concerns and provides clear, manageable implementation path.

---

## ACCEPTANCE
*[To be completed by Alfred Essa after phase execution]*

**Status:** Pending  
**Accepted by:** [Pending]  
**Date:** [Pending]  
**Outcome:** [Pending]  
**Notes:** [Pending]