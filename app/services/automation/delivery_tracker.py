"""Delivery tracking system for preventing duplicate job deliveries."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from sqlalchemy import select, desc

from app.database.session import SessionLocal
from app.models.job import Job
from app.core.logging import logger


@dataclass
class DeliveryRecord:
    """Record of a job delivery."""
    job_url: str
    delivery_date: datetime
    delivery_method: str  # 'telegram', 'email', etc.
    delivery_status: str  # 'success', 'failed', 'retry'
    message_id: Optional[str] = None
    error_message: Optional[str] = None


class DeliveryTracker:
    """Tracks job deliveries to prevent duplicates."""
    
    def __init__(self):
        self.logger = logger.bind(service="delivery_tracker")
        self._delivered_urls: Set[str] = set()
        self._delivery_records: List[DeliveryRecord] = []
        self._loaded = False
    
    async def load_delivered_jobs(
    self,
    days_back: int = 30
) -> None:
        """Load previously delivered jobs from database."""

        try:

            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            async with SessionLocal() as session:

                stmt = (
                    select(Job)
                    .where(Job.posted_at >= cutoff_date)
                    .where(Job.final_score.isnot(None))
                    .order_by(desc(Job.posted_at))
                )

                result = await session.execute(stmt)

                jobs = result.scalars().all()

                for job in jobs:

                    if job.job_url:

                        self._delivered_urls.add(job.job_url)

                self._loaded = True

                self.logger.info(
                    f"Loaded {len(self._delivered_urls)} delivered URLs from last {days_back} days"
                )

        except Exception as e:

            self.logger.error(
                f"Failed to load delivered jobs: {e}"
            )

            self._loaded = False
        
    async def is_job_delivered(self, job_url: str) -> bool:
        """Check if a job has been delivered before."""
        if not self._loaded:
            await self.load_delivered_jobs()
            
        return job_url in self._delivered_urls
    
    async def mark_job_delivered(
        self,
        job_url: str,
        delivery_method: str = "telegram",
        delivery_status: str = "success",
        message_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Mark a job as delivered."""
        try:
            delivery_record = DeliveryRecord(
                job_url=job_url,
                delivery_date=datetime.utcnow(),
                delivery_method=delivery_method,
                delivery_status=delivery_status,
                message_id=message_id,
                error_message=error_message
            )
            
            self._delivery_records.append(delivery_record)
            self._delivered_urls.add(job_url)
            
            self.logger.info(f"Marked job as delivered: {job_url} ({delivery_method}:{delivery_status})")
            
        except Exception as e:
            self.logger.error(f"Failed to mark job as delivered: {e}")
    
    async def filter_undelivered_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out jobs that have already been delivered."""
        if not jobs:
            return []
        
        filtered_jobs = []
        delivered_count = 0
        
        for job in jobs:
            job_url = job.get('job_url', '')
            if job_url:
                if await self.is_job_delivered(job_url):
                    delivered_count += 1
                    continue
                else:
                    filtered_jobs.append(job)
            else:
                # Jobs without URLs are always included
                filtered_jobs.append(job)
        
        self.logger.info(f"Filtered {delivered_count} already delivered jobs from {len(jobs)} total")
        return filtered_jobs
    
    async def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics."""
        if not self._loaded:
            await self.load_delivered_jobs()
        
        stats = {
            'total_delivered': len(self._delivered_urls),
            'delivery_records': len(self._delivery_records),
            'delivered_urls': list(self._delivered_urls)
        }
        
        # Add recent delivery stats
        recent_deliveries = [
            record for record in self._delivery_records
            if record.delivery_date >= datetime.utcnow() - timedelta(days=7)
        ]
        
        stats['recent_deliveries'] = len(recent_deliveries)
        stats['recent_success_rate'] = (
            len([r for r in recent_deliveries if r.delivery_status == 'success']) / 
            len(recent_deliveries) if recent_deliveries else 0
        )
        
        return stats
    
    async def clean_old_records(self, days_to_keep: int = 90) -> None:
        """Clean old delivery records."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Remove old records from memory
            old_records = [
                record for record in self._delivery_records
                if record.delivery_date < cutoff_date
            ]
            
            for record in old_records:
                self._delivery_records.remove(record)
            
            self.logger.info(f"Cleaned {len(old_records)} old delivery records")
            
        except Exception as e:
            self.logger.error(f"Failed to clean old delivery records: {e}")
    
    async def get_failed_deliveries(self, hours_back: int = 24) -> List[DeliveryRecord]:
        """Get failed deliveries for retry."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        failed_deliveries = [
            record for record in self._delivery_records
            if (record.delivery_status == 'failed' and 
                record.delivery_date >= cutoff_time)
        ]
        
        return failed_deliveries
    
    async def retry_failed_deliveries(self, telegram_service) -> int:
        """Retry failed deliveries."""
        failed_deliveries = await self.get_failed_deliveries()
        retried_count = 0
        
        for record in failed_deliveries:
            try:
                # This would need the actual job content to retry
                # For now, just log the retry attempt
                self.logger.info(f"Would retry delivery for: {record.job_url}")
                retried_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to retry delivery: {e}")
        
        return retried_count
    
    def get_delivery_summary(self) -> str:
        """Get a summary of delivery activity."""
        if not self._delivery_records:
            return "No delivery records found."
        
        total = len(self._delivery_records)
        successful = len([r for r in self._delivery_records if r.delivery_status == 'success'])
        failed = len([r for r in self._delivery_records if r.delivery_status == 'failed'])
        
        summary = f"📊 *Delivery Summary*\n"
        summary += f"📦 Total deliveries: {total}\n"
        summary += f"✅ Successful: {successful}\n"
        summary += f"❌ Failed: {failed}\n"
        
        if total > 0:
            success_rate = (successful / total) * 100
            summary += f"📈 Success rate: {success_rate:.1f}%\n"
        
        return summary
    
    async def export_delivery_records(self) -> List[Dict[str, Any]]:
        """Export delivery records for analysis."""
        records = []
        
        for record in self._delivery_records:
            records.append({
                'job_url': record.job_url,
                'delivery_date': record.delivery_date.isoformat(),
                'delivery_method': record.delivery_method,
                'delivery_status': record.delivery_status,
                'message_id': record.message_id,
                'error_message': record.error_message
            })
        
        return records
