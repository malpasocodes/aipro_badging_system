"""Seed catalog with sample badge hierarchy data."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4
from sqlmodel import Session, create_engine

from app.core.config import get_settings
from app.models import Program, Skill, MiniBadge, Capstone


def seed_catalog() -> None:
    """Seed database with sample badge catalog."""
    settings = get_settings()
    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        # Check if catalog already seeded
        existing_programs = session.query(Program).count()
        if existing_programs > 0:
            print(f"Catalog already contains {existing_programs} programs. Skipping seed.")
            return

        print("Seeding catalog with sample data...")

        # Program 1: AI & Python Fundamentals
        program1 = Program(
            id=uuid4(),
            title="AI & Python Fundamentals",
            description="Master the fundamentals of Python programming and AI concepts",
            is_active=True,
            position=0,
        )
        session.add(program1)

        # Skills for Program 1
        skill1_1 = Skill(
            id=uuid4(),
            program_id=program1.id,
            title="Python Basics",
            description="Learn Python syntax, data structures, and control flow",
            is_active=True,
            position=0,
        )
        session.add(skill1_1)

        skill1_2 = Skill(
            id=uuid4(),
            program_id=program1.id,
            title="AI Concepts",
            description="Understand fundamental AI and machine learning concepts",
            is_active=True,
            position=1,
        )
        session.add(skill1_2)

        skill1_3 = Skill(
            id=uuid4(),
            program_id=program1.id,
            title="API Development",
            description="Build RESTful APIs with Python frameworks",
            is_active=True,
            position=2,
        )
        session.add(skill1_3)

        # Mini-badges for Python Basics
        mini_badges_python = [
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_1.id,
                title="Variables and Data Types",
                description="Understand Python variables, strings, numbers, and basic types",
                is_active=True,
                position=0,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_1.id,
                title="Control Flow",
                description="Master if/else, loops, and conditional logic",
                is_active=True,
                position=1,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_1.id,
                title="Functions and Modules",
                description="Write reusable functions and organize code into modules",
                is_active=True,
                position=2,
            ),
        ]
        for mb in mini_badges_python:
            session.add(mb)

        # Mini-badges for AI Concepts
        mini_badges_ai = [
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_2.id,
                title="Machine Learning Basics",
                description="Understand supervised vs unsupervised learning",
                is_active=True,
                position=0,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_2.id,
                title="Neural Networks",
                description="Learn about neural network architecture and training",
                is_active=True,
                position=1,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_2.id,
                title="Prompt Engineering",
                description="Master techniques for working with LLMs",
                is_active=True,
                position=2,
            ),
        ]
        for mb in mini_badges_ai:
            session.add(mb)

        # Mini-badges for API Development
        mini_badges_api = [
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_3.id,
                title="REST API Fundamentals",
                description="Understand HTTP methods, endpoints, and RESTful design",
                is_active=True,
                position=0,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_3.id,
                title="FastAPI Basics",
                description="Build APIs with FastAPI framework",
                is_active=True,
                position=1,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill1_3.id,
                title="API Authentication",
                description="Implement OAuth and JWT authentication",
                is_active=True,
                position=2,
            ),
        ]
        for mb in mini_badges_api:
            session.add(mb)

        # Capstone for Program 1
        capstone1 = Capstone(
            id=uuid4(),
            program_id=program1.id,
            title="AI Application Project",
            description="Build a complete AI-powered application with API backend",
            is_required=False,
            is_active=True,
        )
        session.add(capstone1)

        # Program 2: Data Science Essentials
        program2 = Program(
            id=uuid4(),
            title="Data Science Essentials",
            description="Learn data analysis, visualization, and statistical thinking",
            is_active=True,
            position=1,
        )
        session.add(program2)

        # Skills for Program 2
        skill2_1 = Skill(
            id=uuid4(),
            program_id=program2.id,
            title="Data Analysis with Pandas",
            description="Master data manipulation and analysis with Pandas",
            is_active=True,
            position=0,
        )
        session.add(skill2_1)

        skill2_2 = Skill(
            id=uuid4(),
            program_id=program2.id,
            title="Data Visualization",
            description="Create compelling visualizations with Matplotlib and Plotly",
            is_active=True,
            position=1,
        )
        session.add(skill2_2)

        # Mini-badges for Data Analysis
        mini_badges_pandas = [
            MiniBadge(
                id=uuid4(),
                skill_id=skill2_1.id,
                title="DataFrames and Series",
                description="Work with Pandas data structures",
                is_active=True,
                position=0,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill2_1.id,
                title="Data Cleaning",
                description="Handle missing data, duplicates, and outliers",
                is_active=True,
                position=1,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill2_1.id,
                title="Aggregation and Grouping",
                description="Summarize data with groupby and aggregation functions",
                is_active=True,
                position=2,
            ),
        ]
        for mb in mini_badges_pandas:
            session.add(mb)

        # Mini-badges for Data Visualization
        mini_badges_viz = [
            MiniBadge(
                id=uuid4(),
                skill_id=skill2_2.id,
                title="Chart Types",
                description="Create bar, line, scatter, and other chart types",
                is_active=True,
                position=0,
            ),
            MiniBadge(
                id=uuid4(),
                skill_id=skill2_2.id,
                title="Interactive Visualizations",
                description="Build interactive charts with Plotly",
                is_active=True,
                position=1,
            ),
        ]
        for mb in mini_badges_viz:
            session.add(mb)

        # Commit all changes
        session.commit()

        # Print summary
        program_count = session.query(Program).count()
        skill_count = session.query(Skill).count()
        mini_badge_count = session.query(MiniBadge).count()
        capstone_count = session.query(Capstone).count()

        print(f"✅ Catalog seeded successfully!")
        print(f"  - Programs: {program_count}")
        print(f"  - Skills: {skill_count}")
        print(f"  - Mini-badges: {mini_badge_count}")
        print(f"  - Capstones: {capstone_count}")


if __name__ == "__main__":
    seed_catalog()
