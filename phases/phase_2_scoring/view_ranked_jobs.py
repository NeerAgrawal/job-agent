#!/usr/bin/env python3

"""View ranked jobs from database."""

import asyncio
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, desc

from app.database.session import get_db_session
from app.models.job import Job


async def view_ranked_jobs():
    print("\n" + "=" * 80)
    print("🚀 PM SHORTLIST QUALITY JOBS")
    print("=" * 80)

    async with get_db_session() as session:
        stmt = (
            select(Job)
            .where(Job.final_score.isnot(None))
            .where(Job.final_score >= 45.0)  # Shortlist quality threshold
            .order_by(desc(Job.final_score))
            .limit(15)
        )

        result = await session.execute(stmt)

        jobs = result.scalars().all()

        if not jobs:
            print("\n❌ No ranked jobs found.")
            print("Run AI matching first.")
            return

        for idx, job in enumerate(jobs, start=1):
            print("\n" + "-" * 80)

            print(f"\n#{idx}")
            print(f"🎯 Title: {job.title}")
            print(f"🏢 Company: {job.company}")
            print(f"📍 Location: {job.location}")
            print(
                f"⭐ Final Score: "
                f"{round(job.final_score or 0, 2)}"
            )
            print(
                f"🧠 Semantic Score: "
                f"{round(job.semantic_score or 0, 2)}"
            )
            print(
                f"🔄 Transition Score: "
                f"{round(job.transition_score or 0, 2)}"
            )
            print(
                f"💰 Salary Score: "
                f"{round(job.salary_score or 0, 2)}"
            )
            print(
                f"🌐 Source: {job.source}"
            )
            print(
                f"🏷️ Domain Tags: "
                f"{job.domain_tags}"
            )

            # Calculate recency
            from datetime import datetime, timedelta
            recency_days = None
            recency_label = "Unknown"
            if job.posted_at:
                days_ago = (datetime.utcnow() - job.posted_at).days
                if days_ago <= 1:
                    recency_label = "Today"
                    recency_days = 0
                elif days_ago <= 7:
                    recency_label = "This week"
                    recency_days = days_ago
                elif days_ago <= 30:
                    recency_label = "This month"
                    recency_days = days_ago
                else:
                    recency_label = f"{days_ago} days ago"
                    recency_days = days_ago

            print(
                f"📅 Posted: {recency_label}"
            )

            # Determine PM category
            from app.services.ai.title_filters import get_title_category
            pm_category = get_title_category(job.title)
            pm_category_emoji = {
                "pm": "✅ PM Role",
                "reject": "❌ Non-PM", 
                "unknown": "❓ Unknown"
            }.get(pm_category, "❓ Unknown")

            print(
                f"🎯 Category: {pm_category_emoji}"
            )

            # Salary estimate
            salary_display = "Not specified"
            if job.salary and job.salary > 0:
                if job.salary < 80000:
                    salary_display = f"${int(job.salary/1000)}k-${int(job.salary/5000)}k"
                elif job.salary < 120000:
                    salary_display = f"${int(job.salary/1000)}k-${int(job.salary/5000)}k"
                else:
                    salary_display = f"${int(job.salary/1000)}k+"

            print(
                f"💰 Salary: {salary_display}"
            )

            print(
                f"📝 Match Reason:"
            )

            print(
                f"{job.relevance_reason or 'No reason provided'}"
            )

            print(
                f"\n🔗 URL:"
            )

            print(job.job_url)

        print("\n" + "=" * 80)
        print("✅ Ranked job view completed")
        print("=" * 80)


def main():
    try:
        asyncio.run(view_ranked_jobs())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
