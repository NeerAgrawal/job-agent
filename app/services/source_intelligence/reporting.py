"""Source intelligence reporting system."""

from typing import Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from .analytics import SourceAnalytics


class SourceIntelligenceReporter:
    """Generates comprehensive source intelligence reports."""
    
    def __init__(self):
        self.logger = logger.bind(service="intelligence_reporter")
        self.analytics = SourceAnalytics()
    
    def generate_comprehensive_report(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive source intelligence report."""
        if not source_data:
            return {'status': 'no_data'}
        
        report = {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'report_type': 'comprehensive_source_intelligence',
                'version': 'v0.5-stable-india-foundation'
            },
            'executive_summary': self._generate_executive_summary(source_data),
            'source_performance': self._generate_source_performance_section(source_data),
            'efficiency_analysis': self._generate_efficiency_section(source_data),
            'health_metrics': self._generate_health_metrics_section(source_data),
            'recommendations': self._generate_recommendations_section(source_data),
            'action_items': self._generate_action_items(source_data)
        }
        
        self.logger.info("Generated comprehensive source intelligence report")
        return report
    
    def _generate_executive_summary(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary."""
        total_sources = len(source_data)
        total_fetched = sum(data.get('total_fetched', 0) for data in source_data.values())
        total_pm_accepted = sum(data.get('pm_accepted', 0) for data in source_data.values())
        total_pm_rejected = sum(data.get('pm_rejected', 0) for data in source_data.values())
        
        # Calculate key metrics
        overall_pm_density = (total_pm_accepted / max(total_fetched, 1)) * 100
        avg_quality = sum(float(data.get('quality_score', 0)) for data in source_data.values()) / total_sources if total_sources > 0 else 0
        
        return {
            'total_sources': total_sources,
            'total_jobs_fetched': total_fetched,
            'total_pm_accepted': total_pm_accepted,
            'total_pm_rejected': total_pm_rejected,
            'overall_pm_density': f"{overall_pm_density:.1f}%",
            'average_quality_score': f"{avg_quality:.1f}",
            'system_health': self._assess_system_health(avg_quality, overall_pm_density),
            'key_insights': self._generate_key_insights(source_data),
            'performance_trend': self._calculate_performance_trend(source_data)
        }
    
    def _generate_source_performance_section(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed source performance section."""
        performance_section = {
            'top_performers': self._get_top_performers(source_data),
            'under_performers': self._get_under_performers(source_data),
            'source_rankings': self._rank_sources_by_performance(source_data),
            'performance_distribution': self._analyze_performance_distribution(source_data),
            'source_comparison': self._compare_sources(source_data)
        }
        
        return performance_section
    
    def _generate_efficiency_section(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate efficiency analysis section."""
        from .efficiency import FetchEfficiencyAnalyzer
        
        analyzer = FetchEfficiencyAnalyzer()
        efficiency_analysis = analyzer.analyze_fetch_efficiency(source_data)
        
        return {
            'overall_efficiency': efficiency_analysis.get('overall_efficiency', 'N/A'),
            'waste_analysis': efficiency_analysis.get('waste_ratio', 'N/A'),
            'cost_analysis': efficiency_analysis.get('cost_analysis', {}),
            'optimization_opportunities': efficiency_analysis.get('optimization_opportunities', []),
            'efficiency_grade': efficiency_analysis.get('efficiency_grade', 'N/A')
        }
    
    def _generate_health_metrics_section(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health metrics section."""
        from .source_health import SourceHealthTracker
        
        tracker = SourceHealthTracker()
        
        # Calculate health metrics for each source
        health_metrics = {}
        for source_name, data in source_data.items():
            health_metrics[source_name] = {
                'pm_density': data.get('pm_density', 'N/A'),
                'quality_score': data.get('quality_score', 'N/A'),
                'acceptance_rate': data.get('acceptance_rate', 'N/A'),
                'health_status': self._get_health_status(float(data.get('quality_score', 0))),
                'risk_factors': self._identify_risk_factors(data),
                'stability_indicators': self._assess_stability(data)
            }
        
        return health_metrics
    
    def _generate_recommendations_section(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations section."""
        recommendations = {
            'immediate_actions': self._get_immediate_actions(source_data),
            'strategic_improvements': self._get_strategic_improvements(source_data),
            'source_specific': self._get_source_specific_recommendations(source_data),
            'system_optimizations': self._get_system_optimizations(source_data),
            'long_term_considerations': self._get_long_term_considerations(source_data)
        }
        
        return recommendations
    
    def _generate_action_items(self, source_data: Dict[str, Any]) -> List[str]:
        """Generate actionable items."""
        action_items = []
        
        # Critical actions
        low_density_sources = [
            name for name, data in source_data.items()
            if float(data.get('pm_density', '0').replace('%', '')) < 2
        ]
        
        if low_density_sources:
            action_items.append(f"Review and potentially prune low-density sources: {', '.join(low_density_sources)}")
        
        # High waste sources
        high_waste_sources = [
            name for name, data in source_data.items()
            if int(data.get('pm_rejected', 0)) > int(data.get('total_fetched', 1)) * 0.8
        ]
        
        if high_waste_sources:
            action_items.append(f"Optimize pre-filtering for high-waste sources: {', '.join(high_waste_sources)}")
        
        # Performance issues
        low_quality_sources = [
            name for name, data in source_data.items()
            if float(data.get('quality_score', 0)) < 30
        ]
        
        if low_quality_sources:
            action_items.append(f"Debug and fix low-quality sources: {', '.join(low_quality_sources)}")
        
        if not action_items:
            action_items.append("All sources performing within acceptable parameters")
        
        return action_items
    
    def _get_top_performers(self, source_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get top performing sources."""
        sorted_sources = sorted(
            source_data.items(),
            key=lambda x: float(x[1].get('quality_score', 0)),
            reverse=True
        )
        
        return [
            {
                'source_name': name,
                'quality_score': data.get('quality_score', 0),
                'pm_density': data.get('pm_density', '0'),
                'acceptance_rate': data.get('acceptance_rate', '0'),
                'performance_grade': self._get_performance_grade(float(data.get('quality_score', 0)))
            }
            for name, data in sorted_sources[:5]
        ]
    
    def _get_under_performers(self, source_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get underperforming sources."""
        under_performers = []
        
        for name, data in source_data.items():
            quality_score = float(data.get('quality_score', 0))
            pm_density = float(data.get('pm_density', '0').replace('%', ''))
            
            if quality_score < 40 or pm_density < 3:
                under_performers.append({
                    'source_name': name,
                    'quality_score': quality_score,
                    'pm_density': pm_density,
                    'issues': self._identify_issues(data)
                })
        
        return under_performers
    
    def _rank_sources_by_performance(self, source_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank sources by performance."""
        rankings = []
        
        for name, data in source_data.items():
            quality_score = float(data.get('quality_score', 0))
            pm_density = float(data.get('pm_density', '0').replace('%', ''))
            
            # Calculate composite score
            composite_score = (quality_score * 0.6) + (pm_density * 0.4)
            
            rankings.append({
                'rank': len(rankings) + 1,
                'source_name': name,
                'composite_score': composite_score,
                'quality_score': quality_score,
                'pm_density': pm_density
            })
        
        return sorted(rankings, key=lambda x: x['composite_score'], reverse=True)
    
    def _analyze_performance_distribution(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance distribution."""
        quality_scores = [float(data.get('quality_score', 0)) for data in source_data.values()]
        pm_densities = [float(data.get('pm_density', '0').replace('%', '')) for data in source_data.values()]
        
        return {
            'quality_distribution': {
                'mean': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                'median': sorted(quality_scores)[len(quality_scores)//2] if quality_scores else 0,
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0
            },
            'pm_density_distribution': {
                'mean': sum(pm_densities) / len(pm_densities) if pm_densities else 0,
                'median': sorted(pm_densities)[len(pm_densities)//2] if pm_densities else 0,
                'min': min(pm_densities) if pm_densities else 0,
                'max': max(pm_densities) if pm_densities else 0
            }
        }
    
    def _compare_sources(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare sources against each other."""
        if len(source_data) < 2:
            return {'message': 'Need at least 2 sources for comparison'}
        
        # Find best and worst sources
        best_source = max(source_data.items(), key=lambda x: float(x[1].get('quality_score', 0)))
        worst_source = min(source_data.items(), key=lambda x: float(x[1].get('quality_score', 0)))
        
        return {
            'best_source': {
                'name': best_source[0],
                'quality_score': best_source[1].get('quality_score', 0),
                'pm_density': best_source[1].get('pm_density', '0')
            },
            'worst_source': {
                'name': worst_source[0],
                'quality_score': worst_source[1].get('quality_score', 0),
                'pm_density': worst_source[1].get('pm_density', '0')
            },
            'performance_gap': float(best_source[1].get('quality_score', 0)) - float(worst_source[1].get('quality_score', 0))
        }
    
    def _generate_key_insights(self, source_data: Dict[str, Any]) -> List[str]:
        """Generate key insights from data."""
        insights = []
        
        total_sources = len(source_data)
        high_quality_sources = [
            name for name, data in source_data.items()
            if float(data.get('quality_score', 0)) >= 70
        ]
        
        low_density_sources = [
            name for name, data in source_data.items()
            if float(data.get('pm_density', '0').replace('%', '')) < 3
        ]
        
        insights.append(f"System monitors {total_sources} job sources")
        
        if high_quality_sources:
            insights.append(f"High-quality sources: {', '.join(high_quality_sources)}")
        
        if low_density_sources:
            insights.append(f"Low-density sources: {', '.join(low_density_sources)}")
        
        return insights
    
    def _calculate_performance_trend(self, source_data: Dict[str, Any]) -> str:
        """Calculate overall performance trend."""
        avg_quality = sum(float(data.get('quality_score', 0)) for data in source_data.values()) / len(source_data) if source_data else 0
        
        if avg_quality >= 70:
            return "Improving"
        elif avg_quality >= 50:
            return "Stable"
        elif avg_quality >= 30:
            return "Declining"
        else:
            return "Critical"
    
    def _assess_system_health(self, avg_quality: float, pm_density: float) -> str:
        """Assess overall system health."""
        if avg_quality >= 70 and pm_density >= 5:
            return "Excellent"
        elif avg_quality >= 50 and pm_density >= 3:
            return "Good"
        elif avg_quality >= 30 and pm_density >= 2:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _get_health_status(self, quality_score: float) -> str:
        """Get health status based on quality score."""
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
    
    def _get_performance_grade(self, quality_score: float) -> str:
        """Grade performance based on quality score."""
        if quality_score >= 80:
            return "A"
        elif quality_score >= 70:
            return "B"
        elif quality_score >= 60:
            return "C"
        elif quality_score >= 50:
            return "D"
        else:
            return "F"
    
    def _identify_issues(self, data: Dict[str, Any]) -> List[str]:
        """Identify specific issues with a source."""
        issues = []
        
        quality_score = float(data.get('quality_score', 0))
        pm_density = float(data.get('pm_density', '0').replace('%', ''))
        
        if quality_score < 30:
            issues.append("Very low quality score")
        
        if pm_density < 2:
            issues.append("Very low PM density")
        
        if int(data.get('pm_rejected', 0)) > int(data.get('total_fetched', 1)) * 0.8:
            issues.append("High rejection rate")
        
        return issues
    
    def _assess_stability(self, data: Dict[str, Any]) -> List[str]:
        """Assess source stability indicators."""
        stability = []
        
        # Check for consistent performance
        acceptance_rate = float(data.get('acceptance_rate', '0').replace('%', ''))
        if acceptance_rate >= 60:
            stability.append("Consistent acceptance rate")
        elif acceptance_rate >= 30:
            stability.append("Variable acceptance rate")
        else:
            stability.append("Inconsistent acceptance rate")
        
        # Check for error patterns
        fetch_failures = int(data.get('fetch_failures', 0))
        if fetch_failures == 0:
            stability.append("No fetch failures")
        elif fetch_failures <= 2:
            stability.append("Few fetch failures")
        else:
            stability.append("Multiple fetch failures")
        
        return stability
    
    def _identify_risk_factors(self, data: Dict[str, Any]) -> List[str]:
        """Identify risk factors for a source."""
        risks = []
        
        quality_score = float(data.get('quality_score', 0))
        pm_density = float(data.get('pm_density', '0').replace('%', ''))
        
        if quality_score < 40:
            risks.append("Low quality risk")
        
        if pm_density < 3:
            risks.append("Low signal risk")
        
        if int(data.get('timeouts', 0)) > 3:
            risks.append("Timeout risk")
        
        return risks
    
    def _get_immediate_actions(self, source_data: Dict[str, Any]) -> List[str]:
        """Get immediate action items."""
        actions = []
        
        # Critical issues requiring immediate attention
        critical_sources = [
            name for name, data in source_data.items()
            if float(data.get('quality_score', 0)) < 20
        ]
        
        if critical_sources:
            actions.append(f"URGENT: Fix critical sources: {', '.join(critical_sources)}")
        
        # High waste sources
        high_waste_sources = [
            name for name, data in source_data.items()
            if int(data.get('pm_rejected', 0)) > int(data.get('total_fetched', 1)) * 0.9
        ]
        
        if high_waste_sources:
            actions.append(f"Optimize pre-filtering for high-waste sources: {', '.join(high_waste_sources)}")
        
        return actions
    
    def _get_strategic_improvements(self, source_data: Dict[str, Any]) -> List[str]:
        """Get strategic improvement recommendations."""
        improvements = []
        
        total_sources = len(source_data)
        avg_pm_density = sum(float(data.get('pm_density', '0').replace('%', '')) for data in source_data.values()) / total_sources if total_sources > 0 else 0
        
        if avg_pm_density < 3:
            improvements.append("Focus on high-PM-density sources")
        
        if total_sources > 6:
            improvements.append("Consider source consolidation")
        
        return improvements
    
    def _get_source_specific_recommendations(self, source_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Get source-specific recommendations."""
        recommendations = {}
        
        for name, data in source_data.items():
            source_recs = []
            
            quality_score = float(data.get('quality_score', 0))
            pm_density = float(data.get('pm_density', '0').replace('%', ''))
            
            if quality_score < 50:
                source_recs.append("Review source implementation")
            
            if pm_density < 4:
                source_recs.append("Improve PM targeting")
            
            if int(data.get('invalid_urls', 0)) > 5:
                source_recs.append("Fix URL validation")
            
            recommendations[name] = source_recs
        
        return recommendations
    
    def _get_system_optimizations(self, source_data: Dict[str, Any]) -> List[str]:
        """Get system-level optimization recommendations."""
        optimizations = []
        
        # Check overall system performance
        avg_quality = sum(float(data.get('quality_score', 0)) for data in source_data.values()) / len(source_data) if source_data else 0
        
        if avg_quality < 50:
            optimizations.append("Review overall source quality strategy")
        
        # Check for optimization opportunities
        total_sources = len(source_data)
        if total_sources > 5:
            optimizations.append("Implement source pruning strategy")
        
        return optimizations
    
    def _get_long_term_considerations(self, source_data: Dict[str, Any]) -> List[str]:
        """Get long-term strategic considerations."""
        considerations = []
        
        total_sources = len(source_data)
        high_quality_sources = [
            name for name, data in source_data.items()
            if float(data.get('quality_score', 0)) >= 70
        ]
        
        if len(high_quality_sources) < total_sources * 0.5:
            considerations.append("Invest in source quality improvement")
        
        if total_sources > 4:
            considerations.append("Evaluate source consolidation opportunities")
        
        return considerations
