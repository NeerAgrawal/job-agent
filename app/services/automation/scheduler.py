# -*- coding: utf-8 -*-
"""Daily scheduler for automated job processing and Telegram delivery."""

import asyncio
import os
from datetime import datetime, time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from app.database.session import get_db_session
from app.core.logging import logger
from .telegram import TelegramService
from .digest import DigestFormatter
from .delivery_tracker import DeliveryTracker


@dataclass
class AutomationConfig:
    """Configuration for daily automation."""
    enabled: bool = True
    delivery_hour: int = 9  # 9 AM
    delivery_timezone: str = "UTC"
    max_jobs_per_day: int = 50
    min_score_threshold: float = 60.0
    telegram_enabled: bool = True
    cleanup_enabled: bool = True
    fetch_enabled: bool = True
    scoring_enabled: bool = True
    export_enabled: bool = True


class DailyScheduler:
    """Daily scheduler for automated job processing."""
    
    def __init__(self, config: Optional[AutomationConfig] = None):
        self.logger = logger.bind(service="scheduler")
        self.config = config or self._load_config()
        self.scheduler = AsyncIOScheduler()
        self.telegram_service = TelegramService()
        self.digest_formatter = DigestFormatter()
        self.delivery_tracker = DeliveryTracker()
        self.is_running = False
        self.last_run_time: Optional[datetime] = None
        self.last_run_stats: Dict[str, Any] = {}
        
    def _load_config(self) -> AutomationConfig:
        """Load configuration from environment variables."""
        return AutomationConfig(
            enabled=os.getenv("AUTOMATION_ENABLED", "true").lower() == "true",
            delivery_hour=int(os.getenv("DELIVERY_HOUR", "9")),
            delivery_timezone=os.getenv("DELIVERY_TIMEZONE", "UTC"),
            max_jobs_per_day=int(os.getenv("MAX_JOBS_PER_DAY", "50")),
            min_score_threshold=float(os.getenv("MIN_SCORE_THRESHOLD", "60.0")),
            telegram_enabled=os.getenv("TELEGRAM_ENABLED", "true").lower() == "true",
            cleanup_enabled=os.getenv("CLEANUP_ENABLED", "true").lower() == "true",
            fetch_enabled=os.getenv("FETCH_ENABLED", "true").lower() == "true",
            scoring_enabled=os.getenv("SCORING_ENABLED", "true").lower() == "true",
            export_enabled=os.getenv("EXPORT_ENABLED", "true").lower() == "true"
        )
    
    def start(self) -> None:
        """Start the daily scheduler."""
        try:
            if not self.config.enabled:
                self.logger.info("Automation disabled in configuration")
                return
            
            # Schedule daily job
            self.scheduler.add_job(
                self._run_daily_automation,
                CronTrigger(
                    hour=self.config.delivery_hour,
                    minute=0,
                    timezone=timezone(self.config.delivery_timezone)
                ),
                id="daily_automation",
                name="Daily PM Job Automation",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            self.logger.info(
                f"Daily scheduler started - runs at {self.config.delivery_hour:02d}:00 "
                f"{self.config.delivery_timezone}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            self.is_running = False
    
    def stop(self) -> None:
        """Stop the daily scheduler."""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                self.logger.info("Daily scheduler stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {e}")
    
    async def run_now(self) -> Dict[str, Any]:
        """Run the daily automation immediately."""
        return await self._run_daily_automation()
    
    async def _run_daily_automation(self) -> Dict[str, Any]:
        """Run the complete daily automation pipeline."""
        start_time = datetime.utcnow()
        stats = {
            "start_time": start_time.isoformat(),
            "success": False,
            "steps_completed": [],
            "errors": [],
            "jobs_fetched": 0,
            "jobs_scored": 0,
            "jobs_delivered": 0,
            "telegram_sent": False
        }
        
        try:
            self.logger.info("🚀 Starting daily automation pipeline")
            
            # Step 1: Cleanup old jobs
            if self.config.cleanup_enabled:
                await self._run_cleanup(stats)
            
            # Step 2: Fetch fresh jobs
            if self.config.fetch_enabled:
                await self._run_fetch(stats)
            
            # Step 3: Run AI scoring
            if self.config.scoring_enabled:
                await self._run_scoring(stats)
            
            # Step 4: Generate shortlist and exports
            shortlist_jobs = await self._run_shortlist_generation(stats)
            
            # Step 5: Send Telegram digest
            if self.config.telegram_enabled and shortlist_jobs:
                await self._run_telegram_delivery(shortlist_jobs, stats)
            
            # Mark as successful
            stats["success"] = True
            stats["end_time"] = datetime.utcnow().isoformat()
            stats["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            self.last_run_time = datetime.utcnow()
            self.last_run_stats = stats
            
            self.logger.info(f"✅ Daily automation completed successfully - {stats['jobs_delivered']} jobs delivered")
            
        except Exception as e:
            stats["errors"].append(str(e))
            stats["end_time"] = datetime.utcnow().isoformat()
            stats["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.error(f"❌ Daily automation failed: {e}")
            
        return stats
    
    async def _run_cleanup(self, stats: Dict[str, Any]) -> None:
        """Run job cleanup."""
        try:
            from app.services.shortlist.cleanup import JobCleanup
            
            cleanup = JobCleanup()
            result = await cleanup.cleanup_stale_jobs()
            
            stats["cleanup_result"] = result
            stats["steps_completed"].append("cleanup")
            
            self.logger.info(f"✅ Cleanup completed: {result}")
            
        except Exception as e:
            error_msg = f"Cleanup failed: {e}"
            stats["errors"].append(error_msg)
            self.logger.error(error_msg)
    
    async def _run_fetch(self, stats: Dict[str, Any]) -> None:
        """Run job fetching."""
        try:
            from app.services.fetchers.orchestrator import FetcherOrchestrator
            
            orchestrator = FetcherOrchestrator()
            result = await orchestrator.fetch_from_all_sources(limit=50)
            
            stats["jobs_fetched"] = result.get("saved_count", 0)
            stats["fetch_result"] = result
            stats["steps_completed"].append("fetch")
            
            self.logger.info(f"✅ Fetch completed: {stats['jobs_fetched']} jobs saved")
            
        except Exception as e:
            error_msg = f"Fetch failed: {e}"
            stats["errors"].append(error_msg)
            self.logger.error(error_msg)
    
    async def _run_scoring(self, stats: Dict[str, Any]) -> None:
        """Run AI scoring using local resume or default autonomous fallback."""
        try:
            from app.services.ai.matcher import MatchingEngine
            from app.services.ai.scorer import ScoringEngine
            from app.services.ai.embeddings import EmbeddingsEngine
            from app.repositories.job import JobRepository
            from app.services.ai.resume_parser import ResumeParser
            from app.services.ai.profile_builder import ProfileBuilder
            from app.models.job import Job
            from pathlib import Path
            from sqlalchemy import select
            
            async with get_db_session() as session:
                repo = JobRepository(session)
                
                # 1. Fetch unscored jobs from DB. Cap high enough to score an
                # entire fetch run so nothing is left unscored (and therefore
                # excluded from the shortlist) just because of a low batch cap.
                stmt = select(Job).where(Job.final_score.is_(None)).limit(300)
                result = await session.execute(stmt)
                unscored_jobs = result.scalars().all()
                
                if not unscored_jobs:
                    self.logger.info("No unscored jobs found. Skipping scoring pipeline.")
                    stats["jobs_scored"] = 0
                    stats["steps_completed"].append("scoring")
                    return
                
                self.logger.info(f"Discovered {len(unscored_jobs)} unscored jobs for AI Scoring")
                
                # 2. Build Resume Profile (Custom or Fallback)
                resume_path = Path("data/resume.pdf")
                resume_text = ""
                resume_profile = {}
                
                if resume_path.exists():
                    try:
                        self.logger.info("Found custom resume.pdf at 'data/resume.pdf', building profile...")
                        parser = ResumeParser()
                        builder = ProfileBuilder()
                        
                        # Parse unstructured text
                        resume_data = await parser.parse_resume(str(resume_path))
                        if resume_data:
                            resume_text = resume_data.get("raw_text", "")
                            profile_obj = await builder.build_profile(resume_data)
                            
                            if profile_obj:
                                resume_profile = {
                                    "target_roles": profile_obj.target_roles,
                                    "qa_background": resume_data.get("qa_background", False),
                                    "technical_strength": profile_obj.technical_strength,
                                    "preferred_locations": profile_obj.preferred_locations,
                                    "salary_preferences": profile_obj.salary_preferences
                                }
                    except Exception as ex:
                        self.logger.warning(f"Failed to parse custom resume.pdf: {ex}. Reverting to defaults.")
                
                # Robust autonomous baseline PM profile fallback
                if not resume_text or not resume_profile:
                    self.logger.info("Initializing default autonomous baseline profile for scoring")
                    resume_text = "Experienced Product Manager with 5 years building B2B SaaS platforms, microservices architectures, AI technologies, and Agile Scrum workflows."
                    resume_profile = {
                        "target_roles": ["Product Manager", "Technical Product Manager", "Associate Product Manager"],
                        "qa_background": True,
                        "technical_strength": "moderate",
                        "preferred_locations": ["India", "Remote", "Bangalore"],
                        "salary_preferences": {"target_salary": 80000}
                    }

                # 3. Initialize Embeddings and pre-calculate batch job payloads
                self.logger.info("Generating embeddings for batch scoring...")
                embeddings_engine = EmbeddingsEngine()
                await embeddings_engine.initialize()
                
                resume_embedding = await embeddings_engine.embed_resume(resume_text)
                if resume_embedding is None:
                    raise ValueError("Failed to generate root resume embedding payload")

                # Generate batch embeddings for efficiency
                job_texts = [j.jd_text or f"{j.title} at {j.company}" for j in unscored_jobs]
                job_embeddings = await embeddings_engine.embed_jobs_batch(job_texts)
                
                # 4. Score and Persist Loop
                scorer = ScoringEngine()
                scored_count = 0
                
                for idx, job in enumerate(unscored_jobs):
                    try:
                        # Default similarity if model is offline
                        sim_score = 0.5 
                        if job_embeddings and idx < len(job_embeddings) and job_embeddings[idx] is not None:
                            sim_score = await embeddings_engine.cosine_similarity(resume_embedding, job_embeddings[idx])
                        
                        # Run full weighted scoring
                        score_result = await scorer.score_job(
                            job,
                            resume_profile,
                            sim_score
                        )
                        
                        if score_result:
                            # Map scored results into model repository updates
                            scores_dict = {
                                "semantic": score_result.semantic_score,
                                "final": score_result.final_score,
                                "salary": score_result.salary_score,
                                "transition": score_result.qa_to_pm_score
                            }
                            await repo.update_ai_scores(
                                job.id,
                                scores_dict,
                                score_result.relevance_reason
                            )
                            scored_count += 1
                            self.logger.debug(f"Scored: '{job.title}' -> {score_result.final_score:.1f}")
                        else:
                            # Assign a secure baseline below shortlist threshold for low-quality jobs
                            # so they are not selected again for scoring in next run loops
                            await repo.update_ai_scores(
                                job.id,
                                {"semantic": 0, "final": 35.0, "salary": 0, "transition": 0},
                                "Below minimum quality threshold"
                            )
                            scored_count += 1
                            
                    except Exception as inner_ex:
                        self.logger.warning(f"Failed to assign score to job {job.id}: {inner_ex}")
                
                stats["jobs_scored"] = scored_count
                stats["steps_completed"].append("scoring")
                self.logger.info(f"✅ Scoring loop complete: {scored_count} jobs successfully processed and updated")
            
        except Exception as e:
            error_msg = f"Scoring pipeline failed: {e}"
            stats["errors"].append(error_msg)
            self.logger.exception(error_msg)
    
    async def _run_shortlist_generation(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run shortlist generation and exports."""
        try:
            from app.services.shortlist.generator import ShortlistGenerator
            
            generator = ShortlistGenerator()
            result = await generator.generate_daily_shortlist()
            
            shortlist_jobs = result.get("jobs", [])
            stats["shortlist_count"] = len(shortlist_jobs)
            stats["shortlist_result"] = result
            stats["steps_completed"].append("shortlist")
            
            self.logger.info(f"✅ Shortlist generated: {len(shortlist_jobs)} jobs")
            
            return shortlist_jobs
            
        except Exception as e:
            error_msg = f"Shortlist generation failed: {e}"
            stats["errors"].append(error_msg)
            self.logger.error(error_msg)
            return []
    
    async def _run_telegram_delivery(self, jobs: List[Dict[str, Any]], stats: Dict[str, Any]) -> None:
        """Run Telegram delivery and attach tailored resumes."""
        try:
            if not self.telegram_service.is_enabled():
                self.logger.warning("Telegram service not configured")
                stats["steps_completed"].append("telegram")
                return
            
            # Filter out already delivered jobs
            undelivered_jobs = await self.delivery_tracker.filter_undelivered_jobs(jobs)

            if not undelivered_jobs:
                self.logger.info("No new jobs to deliver")
                stats["steps_completed"].append("telegram")
                return

            # Verify link liveness on the delivery candidates (plus a small buffer to
            # backfill any confirmed-dead ones) so we never deliver an expired posting.
            from app.services.automation.link_verifier import filter_live_jobs
            candidates = undelivered_jobs[: self.config.max_jobs_per_day + 5]
            live_candidates = await filter_live_jobs(candidates)

            # Limit to max jobs per day
            jobs_to_deliver = live_candidates[:self.config.max_jobs_per_day]

            if not jobs_to_deliver:
                self.logger.info("No live jobs to deliver after link verification")
                stats["steps_completed"].append("telegram")
                return
            
            # Format digest
            summary_stats = {
                "total_analyzed": stats.get("jobs_scored", 0),
                "shortlist_count": len(jobs),
                "avg_score": sum(job.get("final_score", 0) for job in jobs) / len(jobs) if jobs else 0,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            digest_text = self.digest_formatter.format_daily_digest(jobs_to_deliver, summary_stats)
            
            # Send the main digest to Telegram
            success = await self.telegram_service.send_long_message(digest_text)
            
            if success:
                # Import Resume Intelligence Engine
                from app.services.ai.resume_intelligence import ResumeIntelligenceEngine
                resume_engine = ResumeIntelligenceEngine()
                
                # Mark jobs as delivered and send customized PDF if score > 80
                for job in jobs_to_deliver:
                    job_id = str(job.get("id", job.get("job_id", "unknown")))
                    final_score = job.get("final_score", 0)
                    
                    if final_score >= 80:
                        self.logger.info(f"High-scoring job detected ({final_score}). Generating tailored resume for {job.get('company')}...")
                        pdf_path = await resume_engine.generate_tailored_resume(
                            job_title=job.get("title", ""),
                            company=job.get("company", ""),
                            jd_text=job.get("jd_text", ""),
                            job_id=job_id
                        )
                        
                        if pdf_path:
                            caption = f"🚀 Tailored Resume Ready!\n*{job.get('title')}* at *{job.get('company')}*\nScore: {final_score:.1f}"
                            await self.telegram_service.send_document(
                                text=caption, 
                                document_path=pdf_path
                            )
                            
                    await self.delivery_tracker.mark_job_delivered(
                        job_url=job.get("job_url", ""),
                        delivery_method="telegram",
                        delivery_status="success"
                    )
                
                stats["jobs_delivered"] = len(jobs_to_deliver)
                stats["telegram_sent"] = True
                stats["steps_completed"].append("telegram")
                
                self.logger.info(f"✅ Telegram delivered: {len(jobs_to_deliver)} jobs")
            else:
                stats["errors"].append("Telegram delivery failed")
                self.logger.error("❌ Telegram delivery failed")
            
        except Exception as e:
            error_msg = f"Telegram delivery failed: {e}"
            stats["errors"].append(error_msg)
            self.logger.error(error_msg)
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "is_running": self.is_running,
            "config": {
                "enabled": self.config.enabled,
                "delivery_hour": self.config.delivery_hour,
                "delivery_timezone": self.config.delivery_timezone,
                "max_jobs_per_day": self.config.max_jobs_per_day,
                "min_score_threshold": self.config.min_score_threshold,
                "telegram_enabled": self.config.telegram_enabled
            },
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_run_stats": self.last_run_stats,
            "next_run_time": self.scheduler.get_job("daily_automation").next_run_time.isoformat() if self.is_running else None
        }
    
    async def test_telegram(self) -> bool:
        """Test Telegram delivery."""
        try:
            if not self.telegram_service.is_enabled():
                self.logger.warning("Telegram service not configured")
                return False
            
            test_digest = self.digest_formatter.format_test_digest()
            success = await self.telegram_service.send_long_message(test_digest)
            
            if success:
                self.logger.info("✅ Telegram test successful")
            else:
                self.logger.error("❌ Telegram test failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Telegram test error: {e}")
            return False
