"""Integration tests for ApplicationWorkflow and DB operations."""

import asyncio
import sys
import os
import unittest
from pathlib import Path
from uuid import uuid4

# Ensure correct pathing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.session import get_db_session
from app.services.resume.workflow import ApplicationWorkflow
from app.models.job import Job
from sqlalchemy import select


class TestApplicationWorkflowIntegration(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        """Create session for verification tests."""
        pass

    async def test_application_lifecycle(self):
        """Verify DB persistence of application records and state changes."""
        async with get_db_session() as session:
            workflow = ApplicationWorkflow(session)
            
            # 1. Retrieve a real job ID from local DB for testing
            stmt = select(Job).limit(1)
            result = await session.execute(stmt)
            job = result.scalars().first()
            
            if not job:
                self.skipTest("No jobs found in database to attach application. Skipping integration.")
                
            print(f"Running integration test against Job: {job.title} ({job.id})")
            
            # 2. Initialize application track draft
            app = await workflow.initialize_application(job.id)
            self.assertIsNotNone(app)
            self.assertEqual(app.job_id, job.id)
            self.assertEqual(app.status, "draft")
            
            # Capture record ID
            app_id = app.id
            
            # 3. Test Transition to 'applied' status
            updated = await workflow.transition_status(
                app_id, 
                "applied", 
                notes="Direct website submission."
            )
            self.assertIsNotNone(updated)
            self.assertEqual(updated.status, "applied")
            self.assertIsNotNone(updated.applied_at)
            self.assertIn("status update to applied", updated.notes)
            
            # 4. Test Transition to 'interview' status
            interview_state = await workflow.transition_status(
                app_id,
                "interview",
                notes="1st round scheduled."
            )
            self.assertEqual(interview_state.status, "interview")
            
            # 5. Verify Statistics rollup
            summary = await workflow.get_pipeline_summary()
            self.assertIn("interview", summary)
            self.assertGreaterEqual(summary["interview"], 1)
            
            # 6. Cleanup (optional, but good to remove test application)
            # We delete manually using session to leave DB clean
            from app.models import Application
            stmt_del = select(Application).where(Application.id == app_id)
            res_app = await session.execute(stmt_del)
            to_del = res_app.scalars().first()
            if to_del:
                await session.delete(to_del)
                await session.commit()
            print("Integration Cleanup Done.")

if __name__ == "__main__":
    unittest.main()
