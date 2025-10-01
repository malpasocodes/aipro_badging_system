"""Migrate Phase 4 badge requests (badge_name) to Phase 5 (mini_badge_id)."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, select

from app.core.config import get_settings
from app.models import Request, MiniBadge, Skill, Program
from app.services import get_catalog_service


def migrate_requests() -> None:
    """
    Migrate Phase 4 requests to Phase 5 catalog structure.

    Strategy:
    1. Find all requests with badge_name but no mini_badge_id
    2. Try to match badge_name to existing catalog mini-badges
    3. If no match, create a "Legacy Badges" program/skill and mini-badge
    4. Update request with mini_badge_id
    """
    settings = get_settings()
    engine = create_engine(settings.database_url)
    catalog_service = get_catalog_service()

    with Session(engine) as session:
        # Get all requests without mini_badge_id
        statement = select(Request).where(Request.mini_badge_id == None)
        requests_to_migrate = session.exec(statement).all()

        if not requests_to_migrate:
            print("✅ No requests to migrate. All requests have mini_badge_id.")
            return

        print(f"Found {len(requests_to_migrate)} requests to migrate")

        # Get or create "Legacy Badges" program and skill
        legacy_program = session.exec(
            select(Program).where(Program.title == "Legacy Badges")
        ).first()

        if not legacy_program:
            print("Creating 'Legacy Badges' program...")
            from uuid import uuid4
            legacy_program = Program(
                id=uuid4(),
                title="Legacy Badges",
                description="Badges migrated from Phase 4 (text-based requests)",
                is_active=True,
                position=999,  # Put at end
            )
            session.add(legacy_program)
            session.commit()
            session.refresh(legacy_program)

        legacy_skill = session.exec(
            select(Skill).where(
                Skill.program_id == legacy_program.id,
                Skill.title == "General"
            )
        ).first()

        if not legacy_skill:
            print("Creating 'General' skill under Legacy Badges...")
            from uuid import uuid4
            legacy_skill = Skill(
                id=uuid4(),
                program_id=legacy_program.id,
                title="General",
                description="General skills from Phase 4 migration",
                is_active=True,
                position=0,
            )
            session.add(legacy_skill)
            session.commit()
            session.refresh(legacy_skill)

        # Track statistics
        matched = 0
        created = 0
        failed = 0
        badge_map = {}  # {badge_name: mini_badge_id}

        for request in requests_to_migrate:
            if not request.badge_name:
                print(f"⚠️  Request {request.id} has no badge_name, skipping")
                failed += 1
                continue

            # Try to find existing mini-badge with matching title
            mini_badge = session.exec(
                select(MiniBadge).where(MiniBadge.title == request.badge_name)
            ).first()

            if mini_badge:
                # Found existing badge - use it
                request.mini_badge_id = mini_badge.id
                matched += 1
                print(f"✓ Matched '{request.badge_name}' to existing badge")
            else:
                # Check if we already created a badge for this name
                if request.badge_name in badge_map:
                    request.mini_badge_id = badge_map[request.badge_name]
                    print(f"✓ Reusing created badge for '{request.badge_name}'")
                else:
                    # Create new mini-badge under legacy skill
                    from uuid import uuid4
                    new_badge = MiniBadge(
                        id=uuid4(),
                        skill_id=legacy_skill.id,
                        title=request.badge_name,
                        description=f"Legacy badge migrated from Phase 4",
                        is_active=True,
                        position=created,
                    )
                    session.add(new_badge)
                    session.commit()
                    session.refresh(new_badge)

                    request.mini_badge_id = new_badge.id
                    badge_map[request.badge_name] = new_badge.id
                    created += 1
                    print(f"+ Created legacy badge: '{request.badge_name}'")

            session.add(request)

        # Commit all updates
        session.commit()

        # Print summary
        print("\n" + "=" * 60)
        print("Migration Summary:")
        print("=" * 60)
        print(f"Total requests migrated: {len(requests_to_migrate)}")
        print(f"  - Matched to existing badges: {matched}")
        print(f"  - Created new legacy badges: {created}")
        print(f"  - Failed: {failed}")
        print("=" * 60)

        if failed == 0:
            print("✅ Migration completed successfully!")
        else:
            print(f"⚠️  Migration completed with {failed} failures")

        # Verify all requests now have mini_badge_id
        remaining = session.exec(
            select(Request).where(Request.mini_badge_id == None)
        ).all()

        if remaining:
            print(f"\n⚠️  WARNING: {len(remaining)} requests still without mini_badge_id")
        else:
            print("\n✅ All requests now have mini_badge_id")


if __name__ == "__main__":
    migrate_requests()
