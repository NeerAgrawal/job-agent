"""Source health tracking system for PM job sources."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.core.logging import logger


@dataclass
class SourceMetrics:
    """Health metrics for individual job sources."""
    source_name: str
    total_fetched: int = 0
    pm_accepted: int = 0
    pm_rejected: int = 0
    duplicates_found: int = 0
    invalid_urls: int = 0
    timeouts: int = 0
    fetch_failures: int = 0
    avg_fetch_duration: float = 0.0
    last_fetch_time: Optional[datetime] = None
    
    @property
    def pm_density(self) -> float:
        """Calculate PM job density percentage."""
        if self.total_fetched == 0:
            return 0.0
        return (self.pm_accepted / self.total_fetched) * 100
    
    @property
    def acceptance_rate(self) -> float:
        """Calculate overall acceptance rate."""
        if self.total_fetched == 0:
            return 0.0
        return ((self.total_fetched - self.pm_rejected) / self.total_fetched) * 100
    
    @property
    def quality_score(self) -> float:
        """Calculate overall source quality score."""
        # Base score from PM density
        score = self.pm_density * 0.4
        
        # Penalty for high rejection rate
        rejection_penalty = min(self.pm_rejected / max(self.total_fetched, 1) * 20, 15)
        score -= rejection_penalty
        
        # Penalty for invalid URLs
        url_penalty = min(self.invalid_urls / max(self.total_fetched, 1) * 10, 5)
        score -= url_penalty
        
        # Penalty for timeouts
        timeout_penalty = min(self.timeouts * 5, 10)
        score -= timeout_penalty
        
        # Penalty for fetch failures
        failure_penalty = min(self.fetch_failures * 3, 8)
        score -= failure_penalty
        
        return max(score, 0)


class SourceHealthTracker:
    """Tracks health and performance of all job sources."""
    
    def __init__(self):
        self.logger = logger.bind(service="source_health")
        self.metrics: Dict[str, SourceMetrics] = {}
        self.fetch_history: List[Dict[str, Any]] = []
    
    def start_fetch(self, source_name: str) -> None:
        """Record start of fetch operation."""
        if source_name not in self.metrics:
            self.metrics[source_name] = SourceMetrics(source_name=source_name)
        
        self.metrics[source_name].last_fetch_time = datetime.utcnow()
        self.logger.info(f"Started fetch from {source_name}")
    
    def record_fetch_result(self, source_name: str, total_fetched: int, pm_accepted: int, 
                        pm_rejected: int, duplicates: int = 0, invalid_urls: int = 0,
                        timeouts: int = 0, fetch_failures: int = 0,
                        duration: float = 0.0) -> None:
        """Record fetch results for a source."""
        if source_name not in self.metrics:
            self.metrics[source_name] = SourceMetrics(source_name=source_name)
        
        metrics = self.metrics[source_name]
        metrics.total_fetched += total_fetched
        metrics.pm_accepted += pm_accepted
        metrics.pm_rejected += pm_rejected
        metrics.duplicates_found += duplicates
        metrics.invalid_urls += invalid_urls
        metrics.timeouts += timeouts
        metrics.fetch_failures += fetch_failures
        
        # Update average duration
        if metrics.avg_fetch_duration == 0:
            metrics.avg_fetch_duration = duration
        else:
            metrics.avg_fetch_duration = (metrics.avg_fetch_duration + duration) / 2
        
        self.logger.info(
            f"Source {source_name}: {total_fetched} fetched, "
            f"{pm_accepted} PM accepted, {pm_rejected} rejected, "
            f"density: {metrics.pm_density:.1f}%, "
            f"quality: {metrics.quality_score:.1f}"
        )
    
    def get_source_summary(self, source_name: str) -> Dict[str, Any]:
        """Get comprehensive summary for a source."""
        if source_name not in self.metrics:
            return {}
        
        metrics = self.metrics[source_name]
        return {
            'source_name': metrics.source_name,
            'total_fetched': metrics.total_fetched,
            'pm_accepted': metrics.pm_accepted,
            'pm_rejected': metrics.pm_rejected,
            'pm_density': f"{metrics.pm_density:.1f}%",
            'acceptance_rate': f"{metrics.acceptance_rate:.1f}%",
            'duplicates_found': metrics.duplicates_found,
            'invalid_urls': metrics.invalid_urls,
            'timeouts': metrics.timeouts,
            'fetch_failures': metrics.fetch_failures,
            'avg_fetch_duration': f"{metrics.avg_fetch_duration:.2f}s",
            'quality_score': f"{metrics.quality_score:.1f}",
            'last_fetch_time': metrics.last_fetch_time.isoformat() if metrics.last_fetch_time else None,
            'health_status': self._get_health_status(metrics.quality_score)
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health of all sources."""
        if not self.metrics:
            return {'status': 'no_data'}
        
        total_sources = len(self.metrics)
        total_fetched = sum(m.total_fetched for m in self.metrics.values())
        total_pm_accepted = sum(m.pm_accepted for m in self.metrics.values())
        total_pm_rejected = sum(m.pm_rejected for m in self.metrics.values())
        avg_quality = sum(m.quality_score for m in self.metrics.values()) / total_sources
        
        return {
            'total_sources': total_sources,
            'total_jobs_fetched': total_fetched,
            'total_pm_accepted': total_pm_accepted,
            'total_pm_rejected': total_pm_rejected,
            'overall_pm_density': f"{(total_pm_accepted / max(total_fetched, 1)) * 100:.1f}%",
            'average_quality_score': f"{avg_quality:.1f}",
            'source_details': {
                name: self.get_source_summary(name)
                for name in self.metrics.keys()
            },
            'recommendations': self._generate_recommendations()
        }
    
    def _get_health_status(self, quality_score: float) -> str:
        """Determine health status based on quality score."""
        if quality_score >= 80:
            return "Excellent"
        elif quality_score >= 60:
            return "Good"
        elif quality_score >= 40:
            return "Fair"
        elif quality_score >= 20:
            return "Poor"
        else:
            return "Critical"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on source health."""
        recommendations = []
        
        for metrics in self.metrics.values():
            if metrics.pm_density < 2:
                recommendations.append(f"Consider pruning {metrics.source_name} - low PM density ({metrics.pm_density:.1f}%)")
            
            if metrics.invalid_urls > metrics.total_fetched * 0.1:
                recommendations.append(f"Fix URL validation in {metrics.source_name} - high invalid URL rate")
            
            if metrics.timeouts > 3:
                recommendations.append(f"Optimize timeout handling for {metrics.source_name}")
            
            if metrics.quality_score < 30:
                recommendations.append(f"Review {metrics.source_name} implementation - poor quality score")
        
        if not recommendations:
            recommendations.append("All sources performing well")
        
        return recommendations
