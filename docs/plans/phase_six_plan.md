# Phase 6 Plan: Earning Logic & Awards

**Project:** AIPPRO Badging System
**Phase:** 6 of 10
**Status:** DRAFT - Pending Approval
**Created:** October 1, 2025
**Author:** Alfred Essa (with Claude Code)

---

## Executive Summary

Phase 6 implements the **Earning Logic & Awards** system - the automatic progression and recognition system that transforms approved requests into earned badges. This phase creates the Award model, implements ProgressService for automatic badge progression, and builds the student progress dashboard.

This is a critical phase that completes the core badge earning workflow. When a student's mini-badge request is approved (Phase 4), the system will automatically create an award record and check if they've completed all requirements for higher-level badges (skills and programs). Students will be able to view their earned badges, track progress toward skills and programs, and see visual representations of their learning journey.

**Key Distinction from Phase 5:** Phase 5 created the badge catalog (what badges exist); Phase 6 implements the earning system (what badges students have earned).

---

## Objectives

### Primary Goals
1. **Implement Award data model** - Track earned badges with timestamps and metadata
2. **Build ProgressService** - Automatic progression logic (mini-badge → skill → program)
3. **Create student progress dashboard** - View earned badges and progress tracking
4. **Implement progression rules** - Skill/program awards based on completion criteria
5. **Build badge display components** - Visual representation of earned badges
6. **Add progress indicators** - Show completion percentages for in-progress skills/programs

### Success Criteria
- Award records created automatically when requests are approved
- Skills awarded automatically when all mini-badges completed
- Programs awarded automatically when all skills completed (+ capstone if required)
- Students can view all earned badges with timestamps
- Progress dashboard shows in-progress and completed skills/programs
- Visual indicators show completion status (0%, 50%, 100%, etc.)
- Comprehensive test coverage (30+ unit tests, 15+ integration tests)
- No retroactive awards (only new approvals trigger progression)
- Audit logging for all automatic awards
- Performance optimized (progression checks complete in <100ms)

---

## Approach

### Architecture & Design Patterns

**Service Layer Pattern:**
- `ProgressService`: Award creation and automatic progression logic
- `AwardService`: CRUD operations for awards (read-only for students, admin can view all)
- Integration with existing `RequestService` for approval triggers

**Data Model Pattern:**
- `Award` model with polymorphic support (mini_badge, skill, or program awards)
- Timestamps for earning tracking and sorting
- Optional metadata for additional context

**Business Rules:**
- **Mini-badge Award**: Created when request is approved
- **Skill Award**: Automatically granted when ALL child mini-badges earned
- **Program Award**: Automatically granted when ALL skills earned (+ capstone if required)
- **No Retroactive**: Only new approvals trigger progression (existing approved requests don't auto-award)
- **Idempotency**: Duplicate awards prevented at database level (unique constraints)

**UI/UX Pattern:**
- Student progress dashboard with three sections:
  1. Earned badges (all awards with timestamps)
  2. In-progress skills/programs (with completion percentages)
  3. Available badges (not yet started from catalog)
- Visual badge representations with completion indicators
- Timeline view of earning history

---

## Detailed Implementation Plan

### Step 1: Award Data Model (app/models/)

**Files to Create:**
- `app/models/award.py` - Award model for earned badges
- Update `app/models/__init__.py` to export Award

**Award Model Schema:**
```python
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class AwardType(str, Enum):
    """Type of badge award."""
    MINI_BADGE = "mini_badge"
    SKILL = "skill"
    PROGRAM = "program"


class Award(SQLModel, table=True):
    """Award model for earned badges."""

    __tablename__ = "awards"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Student who earned the award
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Type of award and reference
    award_type: AwardType = Field(index=True)

    # Polymorphic foreign keys (only one should be set based on award_type)
    mini_badge_id: Optional[UUID] = Field(default=None, foreign_key="mini_badges.id", index=True)
    skill_id: Optional[UUID] = Field(default=None, foreign_key="skills.id", index=True)
    program_id: Optional[UUID] = Field(default=None, foreign_key="programs.id", index=True)

    # Original request that triggered this award (for mini_badges)
    request_id: Optional[UUID] = Field(default=None, foreign_key="requests.id")

    # Award metadata
    awarded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    awarded_by: Optional[UUID] = Field(default=None, foreign_key="users.id")  # For manual awards
    notes: Optional[str] = Field(default=None)  # Optional context

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Unique constraint: user can only earn each badge once
    __table_args__ = (
        # Unique constraint for mini_badge awards
        UniqueConstraint('user_id', 'mini_badge_id', name='uq_user_mini_badge'),
        # Unique constraint for skill awards
        UniqueConstraint('user_id', 'skill_id', name='uq_user_skill'),
        # Unique constraint for program awards
        UniqueConstraint('user_id', 'program_id', name='uq_user_program'),
    )
```

**Validation Rules:**
- Exactly one of `mini_badge_id`, `skill_id`, or `program_id` must be set
- `award_type` must match the set foreign key
- `awarded_by` is optional (null for automatic awards)
- `request_id` only set for mini_badge awards

### Step 2: Database Migration

**Migration Tasks:**
1. Create `awards` table with all columns
2. Add unique constraints (user_id + badge_id combinations)
3. Add foreign key constraints to users, mini_badges, skills, programs, requests
4. Add indexes on user_id, award_type, awarded_at, mini_badge_id, skill_id, program_id

**Commands:**
```bash
# Generate migration
uv run alembic revision --autogenerate -m "Add awards table for earned badges"

# Apply migration
uv run alembic upgrade head
```

### Step 3: ProgressService (app/services/)

**Files to Create:**
- `app/services/progress_service.py` - Award creation and progression logic
- Update `app/services/__init__.py` to export ProgressService

**ProgressService Interface:**
```python
class ProgressService:
    """Service for badge earning and automatic progression."""

    # Core award creation
    def award_mini_badge(
        self,
        user_id: UUID,
        mini_badge_id: UUID,
        request_id: UUID,
        awarded_by: UUID
    ) -> Award:
        """Award a mini-badge to a student and trigger progression checks."""

    def award_skill(
        self,
        user_id: UUID,
        skill_id: UUID,
        awarded_by: Optional[UUID] = None  # None for automatic
    ) -> Award:
        """Award a skill badge (automatic or manual)."""

    def award_program(
        self,
        user_id: UUID,
        program_id: UUID,
        awarded_by: Optional[UUID] = None  # None for automatic
    ) -> Award:
        """Award a program badge (automatic or manual)."""

    # Progression checks
    def check_skill_completion(self, user_id: UUID, skill_id: UUID) -> bool:
        """Check if user has earned all mini-badges for a skill."""

    def check_program_completion(self, user_id: UUID, program_id: UUID) -> bool:
        """Check if user has earned all skills (+ capstone) for a program."""

    # Progress queries
    def get_user_awards(
        self,
        user_id: UUID,
        award_type: Optional[AwardType] = None
    ) -> List[Award]:
        """Get all awards for a user, optionally filtered by type."""

    def get_skill_progress(self, user_id: UUID, skill_id: UUID) -> Dict[str, Any]:
        """Get progress toward a skill (earned mini-badges, total, percentage)."""

    def get_program_progress(self, user_id: UUID, program_id: UUID) -> Dict[str, Any]:
        """Get progress toward a program (earned skills, total, percentage)."""

    def get_all_progress(self, user_id: UUID) -> Dict[str, Any]:
        """Get complete progress summary for a user."""

    # Batch operations
    def trigger_progression_checks(self, user_id: UUID) -> List[Award]:
        """Check all possible progressions for user and award new badges."""
```

**Progression Algorithm:**

When a mini-badge is awarded:
1. Create mini_badge Award record
2. Get the parent skill_id from mini_badge
3. Query all mini_badges for that skill
4. Query all mini_badge awards for user in that skill
5. If counts match → Award skill automatically
6. Get the parent program_id from skill
7. Query all skills for that program
8. Query all skill awards for user in that program
9. Check if program has required capstone
10. If all skills earned (+ capstone if required) → Award program automatically

**Performance Considerations:**
- Use COUNT queries instead of loading all records
- Single transaction for award + progression checks
- Indexes on user_id + badge_id combinations
- Cache skill/program structure (programs rarely change)

### Step 4: Integration with RequestService

**Files to Modify:**
- `app/services/request_service.py` - Add progression trigger in `approve_request()`

**Integration Points:**

```python
# In RequestService.approve_request() after updating request status:

def approve_request(
    self,
    request_id: UUID,
    approver_id: UUID,
    approver_role: UserRole,
    reason: Optional[str] = None,
) -> Request:
    # ... existing approval logic ...

    # After request approved and audit log created:
    if request.mini_badge_id:
        # Award mini-badge and trigger progression
        progress_service = get_progress_service(engine=self.engine)
        try:
            awards = progress_service.award_mini_badge(
                user_id=request.user_id,
                mini_badge_id=request.mini_badge_id,
                request_id=request.id,
                awarded_by=approver_id
            )
            # awards is a list: [mini_badge_award, ?skill_award, ?program_award]

            logger.info(
                "Progression check complete",
                user_id=str(request.user_id),
                mini_badge_id=str(request.mini_badge_id),
                awards_granted=len(awards),
            )
        except Exception as e:
            logger.error(
                "Progression check failed",
                user_id=str(request.user_id),
                error=str(e)
            )
            # Don't fail the approval if progression fails
            # Admin can manually fix awards later

    return request
```

**Error Handling:**
- Progression failures should NOT rollback the approval
- Log errors for manual review
- Admin interface can manually trigger progression checks

### Step 5: Student Progress Dashboard UI

**Files to Create:**
- `app/ui/progress_dashboard.py` - Student progress view
- `app/ui/badge_display.py` - Badge visual components
- Update `app/ui/__init__.py` to export new components

**Progress Dashboard Layout:**

```python
def render_progress_dashboard(user: User) -> None:
    """Render student progress dashboard."""

    st.markdown("## 🏆 My Progress")

    # Get complete progress data
    progress_service = get_progress_service()
    all_progress = progress_service.get_all_progress(user.id)

    # Three tabs: Earned, In Progress, Available
    tab_earned, tab_progress, tab_available = st.tabs([
        f"🎖️ Earned ({all_progress['total_earned']})",
        f"📊 In Progress ({all_progress['in_progress_count']})",
        f"🎯 Available ({all_progress['available_count']})"
    ])

    with tab_earned:
        render_earned_badges(all_progress['earned_awards'])

    with tab_progress:
        render_in_progress(all_progress['in_progress_skills'],
                          all_progress['in_progress_programs'])

    with tab_available:
        render_available_badges(all_progress['available_programs'])
```

**Badge Display Component:**

```python
def render_badge_card(
    badge_type: str,
    title: str,
    description: str,
    earned_at: datetime,
    completion: int = 100  # 0-100 percentage
) -> None:
    """Render a single badge card with visual indicator."""

    with st.container():
        col_icon, col_info, col_status = st.columns([1, 4, 2])

        with col_icon:
            # Visual badge icon based on type and completion
            if completion == 100:
                st.markdown("🏆")  # Gold for earned
            elif completion > 0:
                st.markdown("🥈")  # Silver for in-progress
            else:
                st.markdown("⭕")  # Empty for not started

        with col_info:
            st.markdown(f"**{title}**")
            st.caption(description or "No description")

        with col_status:
            if completion == 100:
                st.success(f"Earned {earned_at.strftime('%Y-%m-%d')}")
            else:
                st.progress(completion / 100.0)
                st.caption(f"{completion}% complete")
```

**In-Progress View:**

```python
def render_in_progress_skill(skill_progress: Dict[str, Any]) -> None:
    """Render progress toward a skill."""

    st.markdown(f"### {skill_progress['skill_title']}")

    earned = skill_progress['earned_count']
    total = skill_progress['total_count']
    percentage = skill_progress['percentage']

    st.progress(percentage / 100.0)
    st.caption(f"{earned}/{total} mini-badges earned ({percentage}%)")

    # Show earned mini-badges with checkmarks
    with st.expander("View Details"):
        for mini_badge in skill_progress['mini_badges']:
            if mini_badge['earned']:
                st.markdown(f"✅ {mini_badge['title']}")
            else:
                st.markdown(f"⬜ {mini_badge['title']}")
```

### Step 6: Admin Award Management (Optional)

**Files to Create:**
- `app/ui/award_management.py` - Admin view of all awards
- Add manual award capability (edge cases)

**Features:**
- View all awards across all students
- Filter by user, badge type, date range
- Manually award badges (for special cases)
- Manually trigger progression checks (for retroactive fixes)
- Award statistics and reporting

**Admin Interface:**

```python
def render_award_management(user: User) -> None:
    """Admin interface for award management."""

    st.markdown("### 🏆 Award Management")

    tab_view, tab_manual, tab_stats = st.tabs([
        "View Awards",
        "Manual Award",
        "Statistics"
    ])

    with tab_view:
        # Filterable table of all awards
        render_awards_table()

    with tab_manual:
        # Form to manually award a badge
        render_manual_award_form(user)

    with tab_stats:
        # Award statistics and charts
        render_award_statistics()
```

### Step 7: Integration with Student Dashboard

**Files to Modify:**
- `app/routers/student.py` - Add progress dashboard to student view

**Integration:**

```python
# In student dashboard router
def render_student_dashboard(user: User):
    # ... existing sections ...

    # Add progress dashboard section
    with st.expander("🏆 My Progress", expanded=True):
        render_progress_dashboard(user)
```

### Step 8: Testing

**Unit Tests (30+):**

**File:** `tests/unit/test_progress_service.py`
- Award creation (mini_badge, skill, program)
- Duplicate award prevention (unique constraints)
- Progression checks (skill completion, program completion)
- Progress queries (get_user_awards, get_skill_progress, get_program_progress)
- Edge cases (partial completion, no awards yet, capstone requirements)
- Authorization checks (student can't award themselves)
- Performance tests (progression checks < 100ms)

**Integration Tests (15+):**

**File:** `tests/integration/test_progression_integration.py`
- End-to-end: Request approved → Mini-badge awarded → Skill auto-awarded
- End-to-end: All skills earned → Program auto-awarded
- Capstone requirement: Program not awarded without capstone
- Multiple students: Progression independent per student
- Concurrent requests: Race conditions handled
- Retroactive: Existing approved requests don't trigger awards
- UI integration: Progress dashboard displays correctly
- Admin manual award: Can manually award any badge
- Progression failure: Approval succeeds even if progression fails

---

## Database Schema Changes

### New Table: awards

```sql
CREATE TABLE awards (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    award_type VARCHAR(20) NOT NULL,
    mini_badge_id UUID REFERENCES mini_badges(id),
    skill_id UUID REFERENCES skills(id),
    program_id UUID REFERENCES programs(id),
    request_id UUID REFERENCES requests(id),
    awarded_at TIMESTAMP NOT NULL,
    awarded_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP NOT NULL,

    -- Indexes
    INDEX idx_awards_user_id (user_id),
    INDEX idx_awards_award_type (award_type),
    INDEX idx_awards_awarded_at (awarded_at),
    INDEX idx_awards_mini_badge_id (mini_badge_id),
    INDEX idx_awards_skill_id (skill_id),
    INDEX idx_awards_program_id (program_id),

    -- Unique constraints (prevent duplicate awards)
    UNIQUE (user_id, mini_badge_id),
    UNIQUE (user_id, skill_id),
    UNIQUE (user_id, program_id),

    -- Check constraint (exactly one badge reference must be set)
    CHECK (
        (award_type = 'mini_badge' AND mini_badge_id IS NOT NULL AND skill_id IS NULL AND program_id IS NULL) OR
        (award_type = 'skill' AND skill_id IS NOT NULL AND mini_badge_id IS NULL AND program_id IS NULL) OR
        (award_type = 'program' AND program_id IS NOT NULL AND mini_badge_id IS NULL AND skill_id IS NULL)
    )
);
```

---

## Business Rules & Logic

### Progression Rules

**Rule 1: Mini-badge Award**
- **Trigger**: Request approved with valid mini_badge_id
- **Action**: Create Award record with award_type='mini_badge'
- **Progression**: Check if all mini-badges in parent skill earned

**Rule 2: Skill Award**
- **Trigger**: Last mini-badge in skill awarded
- **Condition**: COUNT(user mini_badge awards in skill) == COUNT(active mini_badges in skill)
- **Action**: Create Award record with award_type='skill'
- **Progression**: Check if all skills in parent program earned

**Rule 3: Program Award**
- **Trigger**: Last skill in program awarded
- **Condition**:
  - COUNT(user skill awards in program) == COUNT(active skills in program)
  - AND (program.has_capstone == false OR user has capstone award)
- **Action**: Create Award record with award_type='program'

### Edge Cases

1. **Inactive Badges**: Only count active badges in completion checks
2. **Deleted Badges**: Historical awards remain, don't count toward completion
3. **Concurrent Approvals**: Use database unique constraints to prevent duplicate awards
4. **Partial Skill**: If student earned 2/3 mini-badges, skill not awarded yet
5. **Capstone Requirement**: Program awards blocked until capstone completed
6. **Manual Awards**: Admin can manually award any badge (bypasses progression)
7. **Retroactive**: Existing approved requests don't auto-award (manual trigger available)

---

## API & Service Contracts

### ProgressService Public Interface

```python
# Award creation (returns list of all awards granted including automatic progressions)
award_mini_badge(user_id, mini_badge_id, request_id, awarded_by) -> List[Award]

# Progress queries
get_user_awards(user_id, award_type=None) -> List[Award]
get_skill_progress(user_id, skill_id) -> Dict[str, Any]
get_program_progress(user_id, program_id) -> Dict[str, Any]
get_all_progress(user_id) -> Dict[str, Any]

# Admin operations
manually_award_badge(user_id, award_type, badge_id, awarded_by, reason) -> Award
trigger_progression_checks(user_id) -> List[Award]
```

### Progress Data Structure

```python
{
    "total_earned": 15,  # Total awards earned
    "in_progress_count": 3,  # Skills/programs in progress
    "available_count": 5,  # Programs not yet started

    "earned_awards": [
        {
            "award_type": "mini_badge",
            "badge_id": "uuid",
            "title": "String Manipulation",
            "awarded_at": "2025-10-01T12:00:00Z",
            "awarded_by": "approver name"
        },
        # ... more awards
    ],

    "in_progress_skills": [
        {
            "skill_id": "uuid",
            "skill_title": "Variables and Types",
            "program_title": "Python Fundamentals",
            "earned_count": 2,
            "total_count": 3,
            "percentage": 66,
            "mini_badges": [
                {"id": "uuid", "title": "Basic Variables", "earned": True},
                {"id": "uuid", "title": "Type Casting", "earned": True},
                {"id": "uuid", "title": "Advanced Types", "earned": False},
            ]
        }
    ],

    "in_progress_programs": [
        {
            "program_id": "uuid",
            "program_title": "Python Fundamentals",
            "earned_skills": 2,
            "total_skills": 5,
            "percentage": 40,
            "has_capstone": True,
            "capstone_earned": False
        }
    ],

    "available_programs": [
        {
            "program_id": "uuid",
            "program_title": "Advanced Python",
            "total_skills": 4,
            "total_mini_badges": 12
        }
    ]
}
```

---

## UI/UX Design

### Student Progress Dashboard

**Layout:**
```
┌─────────────────────────────────────────────┐
│ 🏆 My Progress                              │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ Tabs: Earned | In Progress | Available │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [Earned Tab]                                │
│ ┌─────────────────────────────────────────┐ │
│ │ 🏆 String Manipulation                  │ │
│ │    Mini-badge in Variables & Types      │ │
│ │    ✅ Earned 2025-10-01                 │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [In Progress Tab]                           │
│ ┌─────────────────────────────────────────┐ │
│ │ Variables and Types (66% complete)      │ │
│ │ ████████████░░░░░░░░                   │ │
│ │ 2/3 mini-badges earned                  │ │
│ │ ✅ Basic Variables                      │ │
│ │ ✅ Type Casting                         │ │
│ │ ⬜ Advanced Types                       │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Visual Design Principles:**
- Clear visual hierarchy (earned > in-progress > available)
- Progress bars for in-progress items
- Badge icons differentiated by type (🏆 program, 🥇 skill, 🎖️ mini-badge)
- Timestamps for earned badges
- Expandable details for progress items

### Admin Award Management

**Layout:**
```
┌─────────────────────────────────────────────┐
│ 🏆 Award Management                         │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ Tabs: View | Manual Award | Statistics │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [View Tab]                                  │
│ Filters: [User ▾] [Badge Type ▾] [Date ▾]  │
│ ┌─────────────────────────────────────────┐ │
│ │ Student     | Badge           | Date    │ │
│ │ john@ex.com | String Manip... | 10/01   │ │
│ │ jane@ex.com | Variables & ... | 10/01   │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [Manual Award Tab]                          │
│ Select Student: [Dropdown]                  │
│ Badge Type: [Mini-badge ▾]                  │
│ Select Badge: [Dropdown]                    │
│ Reason: [Text input]                        │
│ [Award Badge]                               │
└─────────────────────────────────────────────┘
```

---

## Testing Strategy

### Unit Test Coverage (30+ tests)

**ProgressService Tests:**
- `test_award_mini_badge_creates_record`
- `test_award_mini_badge_triggers_skill_check`
- `test_award_skill_creates_record`
- `test_award_skill_triggers_program_check`
- `test_award_program_creates_record`
- `test_duplicate_award_prevented`
- `test_partial_skill_no_award`
- `test_complete_skill_awards_skill`
- `test_partial_program_no_award`
- `test_complete_program_awards_program`
- `test_program_with_capstone_requires_capstone`
- `test_program_without_capstone_no_requirement`
- `test_get_user_awards_empty`
- `test_get_user_awards_multiple_types`
- `test_get_skill_progress_no_awards`
- `test_get_skill_progress_partial`
- `test_get_skill_progress_complete`
- `test_get_program_progress_no_awards`
- `test_get_program_progress_partial`
- `test_get_program_progress_complete`
- `test_get_all_progress_structure`
- `test_manual_award_creates_record`
- `test_manual_award_with_reason`
- `test_progression_check_performance`
- `test_inactive_badges_not_counted`
- `test_concurrent_award_handling`

### Integration Test Coverage (15+ tests)

**End-to-End Progression Tests:**
- `test_approve_request_awards_mini_badge`
- `test_complete_skill_progression`
- `test_complete_program_progression`
- `test_multiple_students_independent_progression`
- `test_capstone_requirement_blocks_program`
- `test_capstone_completion_awards_program`
- `test_manual_award_bypasses_progression`
- `test_retroactive_progression_check`
- `test_progression_failure_doesnt_rollback_approval`
- `test_concurrent_approvals_no_duplicate_awards`
- `test_progress_dashboard_displays_correctly`
- `test_admin_manual_award_workflow`
- `test_inactive_badge_excluded_from_completion`
- `test_audit_logs_for_automatic_awards`
- `test_award_statistics_accuracy`

---

## Performance Considerations

### Query Optimization

**Progression Checks:**
- Use COUNT(*) queries instead of loading all records
- Single query per progression level: `SELECT COUNT(*) FROM awards WHERE user_id=? AND mini_badge_id IN (?)`
- Cache catalog structure (programs/skills/mini-badges rarely change)
- Index on (user_id, mini_badge_id), (user_id, skill_id), (user_id, program_id)

**Progress Dashboard:**
- Single query to get all user awards: `SELECT * FROM awards WHERE user_id=?`
- Join with catalog tables to get badge details
- Compute progress percentages in Python (not in SQL)
- Consider caching progress data in session for repeated views

**Performance Targets:**
- Progression check after approval: < 100ms
- Progress dashboard load: < 500ms
- Award creation: < 50ms

---

## Risks & Mitigation

### Risk 1: Concurrent Approval Race Conditions
**Risk:** Two requests for same skill approved simultaneously → duplicate skill award
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Database unique constraints on (user_id, badge_id)
- Catch duplicate key exceptions in ProgressService
- Transaction isolation for award creation + progression checks

### Risk 2: Progression Failure Blocks Approval
**Risk:** Bug in progression logic causes approval to fail
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Wrap progression in try/except block
- Log errors but don't rollback approval
- Admin interface to manually trigger progression
- Comprehensive test coverage

### Risk 3: Performance Degradation with Scale
**Risk:** Progression checks slow down with large catalogs or many students
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Use COUNT queries (not loading all records)
- Add database indexes
- Performance tests with realistic data volumes
- Consider background job queue for progression (future optimization)

### Risk 4: Retroactive Award Complexity
**Risk:** Students expect automatic awards for previously approved requests
**Likelihood:** High
**Impact:** Low
**Mitigation:**
- Clear communication: only new approvals trigger awards
- Admin tool to manually trigger progression for specific users
- Document the decision in Phase 6 plan

### Risk 5: Capstone Logic Edge Cases
**Risk:** Complex capstone requirement logic causes bugs
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Comprehensive test coverage for capstone scenarios
- Clear documentation of capstone requirement rules
- Admin manual award capability for edge cases

---

## Dependencies

### Phase 5 Deliverables (Required)
- ✅ Program, Skill, MiniBadge, Capstone models
- ✅ CatalogService with hierarchy queries
- ✅ Request model with mini_badge_id field
- ✅ RequestService with approval workflow

### External Dependencies
- SQLModel (ORM)
- Alembic (migrations)
- Streamlit (UI framework)

### Future Phases (Dependent on Phase 6)
- Phase 7: Notifications (notify on auto-award)
- Phase 8: Exports (export earned badges)

---

## Timeline

**Estimated Duration:** 3-4 development sessions

**Breakdown:**
- **Session 1 (Day 1):** Award model + migration + ProgressService core logic (2-3 hours)
- **Session 2 (Day 2):** RequestService integration + unit tests (2-3 hours)
- **Session 3 (Day 3):** Student progress dashboard UI + integration tests (2-3 hours)
- **Session 4 (Day 4, optional):** Admin award management + polish + documentation (1-2 hours)

---

## Acceptance Criteria

### Functional Requirements
- ✅ Award model created with proper foreign keys and unique constraints
- ✅ Alembic migration applied successfully
- ✅ ProgressService implements all public methods
- ✅ Mini-badge awards created automatically when requests approved
- ✅ Skill awards created automatically when all mini-badges earned
- ✅ Program awards created automatically when all skills earned (+ capstone)
- ✅ Duplicate awards prevented by database constraints
- ✅ Student progress dashboard displays earned badges
- ✅ Progress indicators show completion percentages
- ✅ Admin can view all awards across all students
- ✅ Admin can manually award badges (optional feature)

### Non-Functional Requirements
- ✅ 30+ unit tests passing
- ✅ 15+ integration tests passing
- ✅ All Phase 6 tests passing (100%)
- ✅ Progression checks complete in < 100ms
- ✅ Progress dashboard loads in < 500ms
- ✅ Complete audit logging for all awards
- ✅ Error handling prevents approval failures
- ✅ Documentation updated (CLAUDE.md, README)
- ✅ Phase 6 plan approved and accepted

### Quality Gates
- All tests passing
- No regression in existing functionality
- Code review complete
- Performance benchmarks met
- Security review complete (SQL injection, authorization)

---

## Deliverables

### Code Deliverables
1. `app/models/award.py` - Award model
2. `alembic/versions/XXX_add_awards_table.py` - Database migration
3. `app/services/progress_service.py` - Progression logic (400+ lines estimated)
4. `app/ui/progress_dashboard.py` - Student progress view (300+ lines estimated)
5. `app/ui/badge_display.py` - Badge visual components
6. `app/ui/award_management.py` - Admin award management (optional)
7. `tests/unit/test_progress_service.py` - 30+ unit tests
8. `tests/integration/test_progression_integration.py` - 15+ integration tests

### Documentation Deliverables
1. Updated `CLAUDE.md` with Phase 6 completion
2. Updated `README.md` with progression rules
3. `docs/logs/phase_six_outcome.md` - Phase 6 outcome log
4. This plan document with acceptance section

---

## Future Enhancements (Post-Phase 6)

### Phase 7+ Enhancements
- Real-time notifications when badges auto-awarded
- Email notifications for earned badges
- Badge sharing on social media
- Printable badge certificates
- Leaderboard (most badges earned)
- Badge analytics dashboard
- Retroactive award automation (background job)
- Evidence upload for badge requests (out of scope for v1)

### Performance Optimizations
- Background job queue for progression checks
- Redis caching for progress data
- Materialized views for award statistics
- Database read replicas for reporting

---

## Open Questions

1. **Retroactive Awards:** Should existing approved requests automatically award badges?
   - **Decision:** No. Only new approvals trigger awards. Admin can manually trigger if needed.
   - **Rationale:** Simpler implementation, clearer behavior, avoids data migration complexity.

2. **Manual Awards:** Should admins be able to manually award badges?
   - **Decision:** Yes (optional feature). Useful for edge cases and retroactive fixes.
   - **Implementation:** Separate admin UI component, same ProgressService methods.

3. **Badge Revocation:** Should badges be revocable?
   - **Decision:** Out of scope for Phase 6. Consider in future phase.
   - **Rationale:** Requires additional business logic and audit trail.

4. **Multiple Capstones:** Can a program have multiple capstones?
   - **Decision:** Data model supports multiple, but business logic treats as "any capstone required".
   - **Implementation:** Check if at least one capstone earned (not all).

5. **Inactive Badge Handling:** Should inactive badges count toward completion?
   - **Decision:** No. Only active badges count toward completion.
   - **Rationale:** Admins may deactivate outdated badges.

---

## APPROVAL SECTION

**Status:** ✅ APPROVED

**Reviewer:** Alfred Essa
**Approval Date:** October 1, 2025
**Notes:** Plan approved. Proceeding with Phase 6 implementation.

---

## ACCEPTANCE SECTION

**Status:** Not Started

**Accepted By:** [Pending]
**Acceptance Date:** [Pending]

### Completion Summary
[To be completed after phase implementation]

### Deliverables Completed
[To be completed after phase implementation]

### Test Results
[To be completed after phase implementation]

### Issues Resolved
[To be completed after phase implementation]

### Outcome
[To be completed after phase implementation]

---

**Plan prepared by:** Alfred Essa (with Claude Code)
**Date:** October 1, 2025
**Version:** 1.0
