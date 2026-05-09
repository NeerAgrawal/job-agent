"""Source health tracking for India job fetchers."""

from typing import Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.core.logging import logger


@dataclass
class SourceHealthMetrics:
    """Health metrics for job sources."""
    source_name: str
    jobs_fetched: int = 0
    jobs_saved: int = 0
    fetch_success_rate: float = 0.0
    timeout_count: int = 0
    pm_acceptance_rate: float = 0.0
    invalid_url_count: int = 0
    duplicate_count: int = 0
    last_fetch_time: datetime = None
    error_count: int = 0


class SourceHealthTracker:
    """Track health and performance of job sources."""
    
    def __init__(self):
        self.logger = logger.bind(service="source_health")
        self.metrics: Dict[str, SourceHealthMetrics] = {}
    
    def record_fetch_start(self, source_name: str) -> None:
        """Record start of fetch operation."""
        if source_name not in self.metrics:
            self.metrics[source_name] = SourceHealthMetrics(source_name=source_name)
        
        self.metrics[source_name].last_fetch_time = datetime.utcnow()
        self.logger.info(f"Started fetch from {source_name}")
    
    def record_fetch_result(self, source_name: str, jobs_fetched: int, jobs_saved: int, 
                        errors: int = 0, timeout: bool = False) -> None:
        """Record fetch results."""
        if source_name not in self.metrics:
            return
        
        metrics = self.metrics[source_name]
        metrics.jobs_fetched += jobs_fetched
        metrics.jobs_saved += jobs_saved
        metrics.error_count += errors
        
        if timeout:
            metrics.timeout_count += 1
        
        # Calculate rates
        total_jobs = metrics.jobs_fetched
        if total_jobs > 0:
            metrics.fetch_success_rate = (total_jobs - errors) / total_jobs
            metrics.pm_acceptance_rate = jobs_saved / total_jobs
        
        self.logger.info(
            f"Fetch result for {source_name}: {jobs_fetched} fetched, "
            f"{jobs_saved} saved, {errors} errors, "
            f"{metrics.fetch_success_rate:.1%} success rate, "
            f"{metrics.pm_acceptance_rate:.1%} PM acceptance rate"
        )
    
    def record_invalid_url(self, source_name: str) -> None:
        """Record invalid URL rejection."""
        if source_name not in self.metrics:
            return
        
        self.metrics[source_name].invalid_url_count += 1
        self.logger.warning(f"Invalid URL rejected from {source_name}")
    
    def record_duplicate(self, source_name: str) -> None:
        """Record duplicate job rejection."""
        if source_name not in self.metrics:
            return
        
        self.metrics[source_name].duplicate_count += 1
        self.logger.debug(f"Duplicate job rejected from {source_name}")
    
    def get_source_summary(self, source_name: str) -> Dict[str, Any]:
        """Get health summary for a source."""
        if source_name not in self.metrics:
            return {}
        
        metrics = self.metrics[source_name]
        return {
            'source_name': metrics.source_name,
            'jobs_fetched': metrics.jobs_fetched,
            'jobs_saved': metrics.jobs_saved,
            'fetch_success_rate': f"{metrics.fetch_success_rate:.1%}",
            'pm_acceptance_rate': f"{metrics.pm_acceptance_rate:.1%}",
            'timeout_count': metrics.timeout_count,
            'invalid_url_count': metrics.invalid_url_count,
            'duplicate_count': metrics.duplicate_count,
            'last_fetch_time': metrics.last_fetch_time.isoformat() if metrics.last_fetch_time else None,
            'health_score': self._calculate_health_score(metrics)
        }
    
    def _calculate_health_score(self, metrics: SourceHealthMetrics) -> str:
        """Calculate overall health score."""
        score = 100
        
        # Penalize low success rates
        if metrics.fetch_success_rate < 0.8:
            score -= 20
        
        # Penalize low PM acceptance
        if metrics.pm_acceptance_rate < 0.5:
            score -= 15
        
        # Penalize timeouts
        if metrics.timeout_count > 0:
            score -= 10
        
        # Penalize invalid URLs
        if metrics.invalid_url_count > 0:
            score -= 5
        
        # Penalize duplicates
        if metrics.duplicate_count > 0:
            score -= 5
        
        return f"{score}/100"
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health of all sources."""
        if not self.metrics:
            return {}
        
        total_sources = len(self.metrics)
        if total_sources == 0:
            return {'status': 'no_data'}
        
        # Calculate overall metrics
        total_fetched = sum(m.jobs_fetched for m in self.metrics.values())
        total_saved = sum(m.jobs_saved for m in self.metrics.values())
        total_errors = sum(m.error_count for m in self.metrics.values())
        avg_success_rate = sum(m.fetch_success_rate for m in self.metrics.values()) / total_sources
        
        return {
            'total_sources': total_sources,
            'total_jobs_fetched': total_fetched,
            'total_jobs_saved': total_saved,
            'total_errors': total_errors,
            'average_success_rate': f"{avg_success_rate:.1%}",
            'source_details': {
                name: self.get_source_summary(name)
                for name in self.metrics.keys()
            }
        }
