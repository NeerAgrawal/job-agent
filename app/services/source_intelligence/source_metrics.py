"""Source metrics calculator for PM job source analysis."""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.logging import logger


class SourceMetricsCalculator:
    """Calculates comprehensive source metrics."""
    
    def __init__(self):
        self.logger = logger.bind(service="source_metrics")
    
    def calculate_pm_density(self, source_name: str, total_jobs: int, pm_jobs: int) -> float:
        """Calculate PM job density percentage."""
        if total_jobs == 0:
            return 0.0
        
        density = (pm_jobs / total_jobs) * 100
        self.logger.info(f"{source_name} PM density: {pm_jobs}/{total_jobs} = {density:.1f}%")
        return density
    
    def calculate_fetch_waste_ratio(self, source_name: str, rejected: int, total: int) -> float:
        """Calculate fetch waste ratio (rejected/total)."""
        if total == 0:
            return 0.0
        
        waste_ratio = (rejected / total) * 100
        self.logger.info(f"{source_name} waste ratio: {rejected}/{total} = {waste_ratio:.1f}%")
        return waste_ratio
    
    def calculate_source_signal_quality(self, source_name: str, metrics: Dict[str, Any]) -> float:
        """Calculate overall source signal quality score."""
        try:
            # PM density (40% weight)
            pm_density = float(metrics.get('pm_density', '0').replace('%', ''))
            density_score = min(pm_density * 0.4, 40)
            
            # Acceptance rate (25% weight)
            acceptance_rate = float(metrics.get('acceptance_rate', '0').replace('%', ''))
            acceptance_score = min(acceptance_rate * 0.25, 25)
            
            # Quality score (20% weight)
            quality_score = float(metrics.get('quality_score', '0'))
            quality_weighted = min(quality_score * 0.2, 20)
            
            # Duration penalty (10% weight)
            avg_duration = float(metrics.get('avg_fetch_duration', '0').replace('s', ''))
            duration_penalty = max(10 - (avg_duration * 0.5), 0)
            
            # Error penalty (5% weight)
            error_count = int(metrics.get('fetch_failures', 0))
            error_penalty = max(5 - (error_count * 1), 0)
            
            total_score = density_score + acceptance_score + quality_weighted + duration_penalty + error_penalty
            
            self.logger.info(f"{source_name} signal quality: {total_score:.1f}/100")
            return total_score
            
        except Exception as e:
            self.logger.error(f"Failed to calculate signal quality for {source_name}: {e}")
            return 0.0
    
    def identify_noisy_sources(self, source_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify sources with high noise/low signal."""
        noisy_sources = []
        
        for source_name, metrics in source_metrics.items():
            # High waste ratio indicates noise
            waste_ratio = float(metrics.get('pm_rejected', 0)) / max(int(metrics.get('total_fetched', 1)), 1)
            
            # Low PM density indicates noise
            pm_density = float(metrics.get('pm_density', '0').replace('%', ''))
            
            # High error rate indicates noise
            error_rate = int(metrics.get('fetch_failures', 0)) / max(int(metrics.get('total_fetched', 1)), 1)
            
            # Source is noisy if multiple indicators are poor
            if (waste_ratio > 0.8 and pm_density < 5) or error_rate > 0.3:
                noisy_sources.append(source_name)
                self.logger.warning(f"Identified noisy source: {source_name} (waste: {waste_ratio:.1%}, density: {pm_density:.1%})")
        
        return noisy_sources
    
    def identify_low_value_sources(self, source_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify sources with low PM job value."""
        low_value_sources = []
        
        for source_name, metrics in source_metrics.items():
            # Low PM acceptance rate
            pm_accepted = int(metrics.get('pm_accepted', 0))
            total_fetched = int(metrics.get('total_fetched', 1))
            acceptance_rate = pm_accepted / total_fetched
            
            # Low average score
            avg_score = float(metrics.get('avg_score', 0))
            
            # High duplicate rate
            duplicate_rate = int(metrics.get('duplicates_found', 0)) / total_fetched
            
            # Source is low value if acceptance < 2% or avg score < 30
            if acceptance_rate < 0.02 or avg_score < 30:
                low_value_sources.append(source_name)
                self.logger.warning(f"Identified low-value source: {source_name} (acceptance: {acceptance_rate:.1%}, avg_score: {avg_score})")
        
        return low_value_sources
    
    def calculate_runtime_cost_analysis(self, source_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze runtime cost efficiency of sources."""
        cost_analysis = {}
        
        for source_name, metrics in source_metrics.items():
            # Calculate cost per PM job
            pm_jobs = int(metrics.get('pm_accepted', 0))
            total_jobs = int(metrics.get('total_fetched', 1))
            avg_duration = float(metrics.get('avg_fetch_duration', '0').replace('s', ''))
            
            cost_per_pm = (total_jobs * avg_duration) / max(pm_jobs, 1)
            
            # Calculate efficiency score
            efficiency = (pm_jobs / total_jobs) * (100 / max(avg_duration, 1))
            
            cost_analysis[source_name] = {
                'cost_per_pm_job': f"{cost_per_pm:.2f}s",
                'efficiency_score': f"{efficiency:.1f}",
                'runtime_cost': 'High' if cost_per_pm > 50 else 'Medium' if cost_per_pm > 20 else 'Low'
            }
        
        return cost_analysis
