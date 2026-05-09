"""Source analytics and reporting system."""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.logging import logger
from .source_health import SourceHealthTracker
from .source_metrics import SourceMetricsCalculator
from .source_weights import SourceWeightManager


class SourceAnalytics:
    """Comprehensive analytics for PM job sources."""
    
    def __init__(self):
        self.logger = logger.bind(service="source_analytics")
        self.health_tracker = SourceHealthTracker()
        self.metrics_calculator = SourceMetricsCalculator()
        self.weight_manager = SourceWeightManager()
    
    def generate_performance_report(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not source_data:
            return {'status': 'no_data'}
        
        report = {
            'report_generated': datetime.utcnow().isoformat(),
            'summary': self._generate_summary(source_data),
            'source_analysis': self._analyze_sources(source_data),
            'recommendations': self._generate_recommendations(source_data),
            'trends': self._analyze_trends(source_data)
        }
        
        self.logger.info("Generated comprehensive source performance report")
        return report
    
    def _generate_summary(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary."""
        total_sources = len(source_data)
        total_fetched = sum(data.get('total_fetched', 0) for data in source_data.values())
        total_pm_accepted = sum(data.get('pm_accepted', 0) for data in source_data.values())
        total_pm_rejected = sum(data.get('pm_rejected', 0) for data in source_data.values())
        
        # Calculate averages
        avg_pm_density = sum(float(data.get('pm_density', '0').replace('%', '')) for data in source_data.values()) / total_sources if total_sources > 0 else 0
        avg_quality_score = sum(float(data.get('quality_score', '0')) for data in source_data.values()) / total_sources if total_sources > 0 else 0
        
        return {
            'total_sources': total_sources,
            'total_jobs_fetched': total_fetched,
            'total_pm_accepted': total_pm_accepted,
            'total_pm_rejected': total_pm_rejected,
            'overall_pm_density': f"{avg_pm_density:.1f}%",
            'average_quality_score': f"{avg_quality_score:.1f}",
            'fetch_efficiency': self._calculate_efficiency(total_pm_accepted, total_fetched),
            'system_health': self._assess_system_health(avg_quality_score, avg_pm_density)
        }
    
    def _analyze_sources(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed analysis of each source."""
        analysis = {}
        
        for source_name, data in source_data.items():
            pm_density = float(data.get('pm_density', '0').replace('%', ''))
            quality_score = float(data.get('quality_score', '0'))
            acceptance_rate = float(data.get('acceptance_rate', '0').replace('%', ''))
            
            # Categorize source performance
            performance_tier = self._get_performance_tier(quality_score, pm_density)
            
            analysis[source_name] = {
                'performance_tier': performance_tier,
                'pm_density_grade': self._get_density_grade(pm_density),
                'quality_grade': self._get_quality_grade(quality_score),
                'acceptance_grade': self._get_acceptance_grade(acceptance_rate),
                'recommendations': self._get_source_recommendations(data, performance_tier)
            }
        
        return analysis
    
    def _generate_recommendations(self, source_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Analyze overall patterns
        low_density_sources = [
            name for name, data in source_data.items()
            if float(data.get('pm_density', '0').replace('%', '')) < 2
        ]
        
        low_quality_sources = [
            name for name, data in source_data.items()
            if float(data.get('quality_score', '0')) < 30
        ]
        
        high_rejection_sources = [
            name for name, data in source_data.items()
            if float(data.get('acceptance_rate', '0').replace('%', '')) < 10
        ]
        
        # Generate specific recommendations
        if low_density_sources:
            recommendations.append(
                f"Consider pruning low-density sources: {', '.join(low_density_sources)} "
                f"(PM density < 2%)"
            )
        
        if low_quality_sources:
            recommendations.append(
                f"Review implementation for low-quality sources: {', '.join(low_quality_sources)} "
                f"(quality score < 30)"
            )
        
        if high_rejection_sources:
            recommendations.append(
                f"Optimize pre-filtering for high-rejection sources: {', '.join(high_rejection_sources)} "
                f"(acceptance rate < 10%)"
            )
        
        # Positive recommendations
        if not recommendations:
            recommendations.append("All sources performing within acceptable ranges")
        
        return recommendations
    
    def _analyze_trends(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends and patterns."""
        trends = {
            'best_performers': [],
            'worst_performers': [],
            'density_distribution': {},
            'quality_distribution': {}
        }
        
        # Sort sources by performance
        sorted_sources = sorted(
            source_data.items(),
            key=lambda x: float(x[1].get('quality_score', 0)),
            reverse=True
        )
        
        # Best performers (top 3)
        trends['best_performers'] = [
            {
                'source_name': name,
                'quality_score': data.get('quality_score', 0),
                'pm_density': data.get('pm_density', '0')
            }
            for name, data in sorted_sources[:3]
        ]
        
        # Worst performers (bottom 3)
        trends['worst_performers'] = [
            {
                'source_name': name,
                'quality_score': data.get('quality_score', 0),
                'pm_density': data.get('pm_density', '0')
            }
            for name, data in sorted_sources[-3:]
        ]
        
        # Distribution analysis
        density_ranges = {'Low': 0, 'Medium': 0, 'High': 0}
        quality_ranges = {'Poor': 0, 'Fair': 0, 'Good': 0, 'Excellent': 0}
        
        for data in source_data.values():
            density = float(data.get('pm_density', '0').replace('%', ''))
            quality = float(data.get('quality_score', 0))
            
            # Density distribution
            if density < 2:
                density_ranges['Low'] += 1
            elif density < 5:
                density_ranges['Medium'] += 1
            else:
                density_ranges['High'] += 1
            
            # Quality distribution
            if quality < 30:
                quality_ranges['Poor'] += 1
            elif quality < 60:
                quality_ranges['Fair'] += 1
            elif quality < 80:
                quality_ranges['Good'] += 1
            else:
                quality_ranges['Excellent'] += 1
        
        trends['density_distribution'] = density_ranges
        trends['quality_distribution'] = quality_ranges
        
        return trends
    
    def _calculate_efficiency(self, pm_accepted: int, total_fetched: int) -> str:
        """Calculate overall fetch efficiency."""
        if total_fetched == 0:
            return "No data"
        
        efficiency = (pm_accepted / total_fetched) * 100
        
        if efficiency >= 50:
            return "Excellent"
        elif efficiency >= 30:
            return "Good"
        elif efficiency >= 15:
            return "Fair"
        else:
            return "Poor"
    
    def _assess_system_health(self, avg_quality: float, avg_density: float) -> str:
        """Assess overall system health."""
        if avg_quality >= 70 and avg_density >= 3:
            return "Excellent"
        elif avg_quality >= 50 and avg_density >= 2:
            return "Good"
        elif avg_quality >= 30 and avg_density >= 1:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _get_performance_tier(self, quality_score: float, pm_density: float) -> str:
        """Determine performance tier."""
        if quality_score >= 70 and pm_density >= 5:
            return "Top Performer"
        elif quality_score >= 50 and pm_density >= 3:
            return "Strong Performer"
        elif quality_score >= 30 and pm_density >= 2:
            return "Average Performer"
        else:
            return "Under Performer"
    
    def _get_density_grade(self, density: float) -> str:
        """Grade PM density."""
        if density >= 5:
            return "A+"
        elif density >= 3:
            return "A"
        elif density >= 2:
            return "B"
        else:
            return "C"
    
    def _get_quality_grade(self, quality: float) -> str:
        """Grade quality score."""
        if quality >= 80:
            return "A"
        elif quality >= 60:
            return "B"
        elif quality >= 40:
            return "C"
        else:
            return "D"
    
    def _get_acceptance_grade(self, acceptance_rate: float) -> str:
        """Grade acceptance rate."""
        if acceptance_rate >= 80:
            return "A+"
        elif acceptance_rate >= 60:
            return "A"
        elif acceptance_rate >= 40:
            return "B"
        else:
            return "C"
    
    def _get_source_recommendations(self, data: Dict[str, Any], tier: str) -> List[str]:
        """Get specific recommendations for a source."""
        recommendations = []
        
        if tier == "Under Performer":
            recommendations.extend([
                "Review source implementation",
                "Check for API issues",
                "Consider source replacement"
            ])
        elif tier == "Average Performer":
            recommendations.extend([
                "Optimize parsing logic",
                "Improve PM filtering",
                "Check timeout settings"
            ])
        elif tier == "Strong Performer":
            recommendations.extend([
                "Maintain current approach",
                "Monitor for degradation"
            ])
        else:  # Top Performer
            recommendations.extend([
                "Use as reference implementation",
                "Consider scaling similar sources"
            ])
        
        return recommendations
