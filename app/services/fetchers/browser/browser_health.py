"""Browser health tracking system for automation monitoring."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.core.logging import logger


@dataclass
class BrowserMetrics:
    """Health metrics for browser automation."""
    source_name: str
    browser_sessions: int = 0
    login_attempts: int = 0
    login_successes: int = 0
    session_reuses: int = 0
    browser_crashes: int = 0
    timeout_count: int = 0
    extraction_failures: int = 0
    total_jobs_extracted: int = 0
    pm_jobs_extracted: int = 0
    avg_session_duration: float = 0.0
    last_browser_run: datetime = None
    
    @property
    def login_success_rate(self) -> float:
        """Calculate login success rate."""
        if self.login_attempts == 0:
            return 0.0
        return (self.login_successes / self.login_attempts) * 100
    
    @property
    def session_reuse_rate(self) -> float:
        """Calculate session reuse rate."""
        if self.browser_sessions == 0:
            return 0.0
        return (self.session_reuses / self.browser_sessions) * 100
    
    @property
    def pm_extraction_rate(self) -> float:
        """Calculate PM job extraction rate."""
        if self.total_jobs_extracted == 0:
            return 0.0
        return (self.pm_jobs_extracted / self.total_jobs_extracted) * 100
    
    @property
    def browser_stability_score(self) -> float:
        """Calculate overall browser stability score."""
        score = 100
        
        # Penalize login failures
        if self.login_attempts > 0:
            login_failure_rate = 1 - (self.login_successes / self.login_attempts)
            score -= login_failure_rate * 30
        
        # Penalize crashes
        if self.browser_sessions > 0:
            crash_rate = self.browser_crashes / self.browser_sessions
            score -= crash_rate * 40
        
        # Penalize timeouts
        if self.browser_sessions > 0:
            timeout_rate = self.timeout_count / self.browser_sessions
            score -= timeout_rate * 20
        
        # Penalize extraction failures
        if self.browser_sessions > 0:
            extraction_failure_rate = self.extraction_failures / self.browser_sessions
            score -= extraction_failure_rate * 10
        
        return max(score, 0)


class BrowserHealthTracker:
    """Tracks health and performance of browser automation."""
    
    def __init__(self):
        self.logger = logger.bind(service="browser_health")
        self.metrics: Dict[str, BrowserMetrics] = {}
        self.session_history: List[Dict[str, Any]] = []
    
    def start_browser_session(self, source_name: str) -> str:
        """Record start of browser session."""
        session_id = f"{source_name}_{datetime.utcnow().timestamp()}"
        
        if source_name not in self.metrics:
            self.metrics[source_name] = BrowserMetrics(source_name=source_name)
        
        self.metrics[source_name].browser_sessions += 1
        self.metrics[source_name].last_browser_run = datetime.utcnow()
        
        # Record session start
        self.session_history.append({
            'session_id': session_id,
            'source_name': source_name,
            'start_time': datetime.utcnow().isoformat(),
            'status': 'started'
        })
        
        self.logger.info(f"Started browser session for {source_name}: {session_id}")
        return session_id
    
    def record_login_attempt(self, source_name: str, success: bool, reused_session: bool = False) -> None:
        """Record login attempt result."""
        if source_name not in self.metrics:
            return
        
        metrics = self.metrics[source_name]
        metrics.login_attempts += 1
        
        if success:
            metrics.login_successes += 1
            if reused_session:
                metrics.session_reuses += 1
        
        self.logger.info(
            f"Login attempt for {source_name}: "
            f"{'success' if success else 'failure'}, "
            f"reused_session={reused_session}"
        )
    
    def record_browser_crash(self, source_name: str, session_id: str) -> None:
        """Record browser crash."""
        if source_name not in self.metrics:
            return
        
        self.metrics[source_name].browser_crashes += 1
        
        # Update session history
        for session in self.session_history:
            if session['session_id'] == session_id:
                session['status'] = 'crashed'
                session['end_time'] = datetime.utcnow().isoformat()
                break
        
        self.logger.error(f"Browser crash recorded for {source_name}: {session_id}")
    
    def record_timeout(self, source_name: str, session_id: str) -> None:
        """Record browser timeout."""
        if source_name not in self.metrics:
            return
        
        self.metrics[source_name].timeout_count += 1
        
        # Update session history
        for session in self.session_history:
            if session['session_id'] == session_id:
                session['status'] = 'timeout'
                session['end_time'] = datetime.utcnow().isoformat()
                break
        
        self.logger.warning(f"Browser timeout recorded for {source_name}: {session_id}")
    
    def record_extraction_results(self, source_name: str, total_jobs: int, pm_jobs: int, 
                                 extraction_failures: int = 0, session_duration: float = 0.0) -> None:
        """Record job extraction results."""
        if source_name not in self.metrics:
            return
        
        metrics = self.metrics[source_name]
        metrics.total_jobs_extracted += total_jobs
        metrics.pm_jobs_extracted += pm_jobs
        metrics.extraction_failures += extraction_failures
        
        # Update average session duration
        if metrics.avg_session_duration == 0:
            metrics.avg_session_duration = session_duration
        else:
            metrics.avg_session_duration = (metrics.avg_session_duration + session_duration) / 2
        
        self.logger.info(
            f"Extraction results for {source_name}: "
            f"{total_jobs} total, {pm_jobs} PM jobs, "
            f"{extraction_failures} failures, "
            f"duration: {session_duration:.2f}s"
        )
    
    def end_browser_session(self, source_name: str, session_id: str, status: str = 'completed') -> None:
        """Record end of browser session."""
        # Update session history
        for session in self.session_history:
            if session['session_id'] == session_id:
                session['status'] = status
                session['end_time'] = datetime.utcnow().isoformat()
                break
        
        self.logger.info(f"Ended browser session for {source_name}: {session_id} - {status}")
    
    def get_source_health(self, source_name: str) -> Dict[str, Any]:
        """Get health summary for a browser source."""
        if source_name not in self.metrics:
            return {}
        
        metrics = self.metrics[source_name]
        return {
            'source_name': metrics.source_name,
            'browser_sessions': metrics.browser_sessions,
            'login_attempts': metrics.login_attempts,
            'login_successes': metrics.login_successes,
            'login_success_rate': f"{metrics.login_success_rate:.1f}%",
            'session_reuses': metrics.session_reuses,
            'session_reuse_rate': f"{metrics.session_reuse_rate:.1f}%",
            'browser_crashes': metrics.browser_crashes,
            'timeout_count': metrics.timeout_count,
            'extraction_failures': metrics.extraction_failures,
            'total_jobs_extracted': metrics.total_jobs_extracted,
            'pm_jobs_extracted': metrics.pm_jobs_extracted,
            'pm_extraction_rate': f"{metrics.pm_extraction_rate:.1f}%",
            'avg_session_duration': f"{metrics.avg_session_duration:.2f}s",
            'browser_stability_score': f"{metrics.browser_stability_score:.1f}",
            'last_browser_run': metrics.last_browser_run.isoformat() if metrics.last_browser_run else None,
            'health_status': self._get_health_status(metrics.browser_stability_score)
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health of browser automation."""
        if not self.metrics:
            return {'status': 'no_data'}
        
        total_sources = len(self.metrics)
        total_sessions = sum(m.browser_sessions for m in self.metrics.values())
        total_login_attempts = sum(m.login_attempts for m in self.metrics.values())
        total_login_successes = sum(m.login_successes for m in self.metrics.values())
        total_jobs_extracted = sum(m.total_jobs_extracted for m in self.metrics.values())
        total_pm_jobs = sum(m.pm_jobs_extracted for m in self.metrics.values())
        total_crashes = sum(m.browser_crashes for m in self.metrics.values())
        total_timeouts = sum(m.timeout_count for m in self.metrics.values())
        
        # Calculate averages
        avg_login_success_rate = (total_login_successes / max(total_login_attempts, 1)) * 100
        avg_pm_extraction_rate = (total_pm_jobs / max(total_jobs_extracted, 1)) * 100
        avg_stability_score = sum(m.browser_stability_score for m in self.metrics.values()) / total_sources
        
        return {
            'total_sources': total_sources,
            'total_sessions': total_sessions,
            'total_login_attempts': total_login_attempts,
            'total_login_successes': total_login_successes,
            'overall_login_success_rate': f"{avg_login_success_rate:.1f}%",
            'total_jobs_extracted': total_jobs_extracted,
            'total_pm_jobs_extracted': total_pm_jobs,
            'overall_pm_extraction_rate': f"{avg_pm_extraction_rate:.1f}%",
            'total_crashes': total_crashes,
            'total_timeouts': total_timeouts,
            'average_stability_score': f"{avg_stability_score:.1f}",
            'source_details': {
                name: self.get_source_health(name)
                for name in self.metrics.keys()
            },
            'recommendations': self._generate_recommendations(),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _get_health_status(self, stability_score: float) -> str:
        """Determine health status based on stability score."""
        if stability_score >= 90:
            return "Excellent"
        elif stability_score >= 75:
            return "Good"
        elif stability_score >= 60:
            return "Fair"
        elif stability_score >= 40:
            return "Poor"
        else:
            return "Critical"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health metrics."""
        recommendations = []
        
        for metrics in self.metrics.values():
            if metrics.login_success_rate < 70:
                recommendations.append(f"Review authentication for {metrics.source_name} - low login success rate")
            
            if metrics.browser_crashes > metrics.browser_sessions * 0.3:
                recommendations.append(f"Investigate browser stability for {metrics.source_name} - high crash rate")
            
            if metrics.timeout_count > metrics.browser_sessions * 0.5:
                recommendations.append(f"Optimize timeout settings for {metrics.source_name} - high timeout rate")
            
            if metrics.pm_extraction_rate < 20:
                recommendations.append(f"Review job extraction logic for {metrics.source_name} - low PM extraction rate")
        
        if not recommendations:
            recommendations.append("All browser sources performing well")
        
        return recommendations
    
    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """Clean up old session history."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        original_count = len(self.session_history)
        
        self.session_history = [
            session for session in self.session_history
            if datetime.fromisoformat(session['start_time']) > cutoff_date
        ]
        
        cleaned_count = original_count - len(self.session_history)
        self.logger.info(f"Cleaned up {cleaned_count} old browser sessions")
        
        return cleaned_count
