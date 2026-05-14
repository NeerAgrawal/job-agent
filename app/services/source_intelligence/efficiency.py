"""Fetch efficiency analysis and optimization."""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.logging import logger


class FetchEfficiencyAnalyzer:
    """Analyzes and optimizes fetch efficiency."""
    
    def __init__(self):
        self.logger = logger.bind(service="efficiency_analyzer")
    
    def analyze_fetch_efficiency(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall fetch efficiency across all sources."""
        if not source_data:
            return {'status': 'no_data'}
        
        total_sources = len(source_data)
        total_fetched = sum(data.get('total_fetched', 0) for data in source_data.values())
        total_accepted = sum(data.get('pm_accepted', 0) for data in source_data.values())
        total_rejected = sum(data.get('pm_rejected', 0) for data in source_data.values())
        
        # Calculate efficiency metrics
        overall_efficiency = (total_accepted / total_fetched) * 100 if total_fetched > 0 else 0
        waste_ratio = (total_rejected / total_fetched) * 100 if total_fetched > 0 else 0
        
        # Identify efficiency patterns
        efficiency_analysis = {
            'total_sources': total_sources,
            'total_fetched': total_fetched,
            'total_accepted': total_accepted,
            'total_rejected': total_rejected,
            'overall_efficiency': f"{overall_efficiency:.1f}%",
            'waste_ratio': f"{waste_ratio:.1f}%",
            'efficiency_grade': self._get_efficiency_grade(overall_efficiency),
            'source_efficiency': self._analyze_source_efficiency(source_data),
            'optimization_opportunities': self._identify_optimization_opportunities(source_data),
            'cost_analysis': self._analyze_fetch_costs(source_data)
        }
        
        self.logger.info(
            f"Fetch efficiency analysis: {overall_efficiency:.1f}% efficiency, "
            f"{waste_ratio:.1f}% waste ratio"
        )
        
        return efficiency_analysis
    
    def _analyze_source_efficiency(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze efficiency per source."""
        source_efficiency = {}
        
        for source_name, data in source_data.items():
            fetched = data.get('total_fetched', 0)
            accepted = data.get('pm_accepted', 0)
            rejected = data.get('pm_rejected', 0)
            
            # Calculate source-specific efficiency
            efficiency = (accepted / fetched) * 100 if fetched > 0 else 0
            waste_ratio = (rejected / fetched) * 100 if fetched > 0 else 0
            
            # Determine efficiency category
            efficiency_category = self._categorize_efficiency(efficiency)
            
            source_efficiency[source_name] = {
                'efficiency': f"{efficiency:.1f}%",
                'waste_ratio': f"{waste_ratio:.1f}%",
                'category': efficiency_category,
                'performance_trend': self._calculate_trend(data),
                'optimization_priority': self._get_optimization_priority(efficiency, waste_ratio)
            }
        
        return source_efficiency
    
    def _categorize_efficiency(self, efficiency: float) -> str:
        """Categorize efficiency level."""
        if efficiency >= 50:
            return "Highly Efficient"
        elif efficiency >= 30:
            return "Efficient"
        elif efficiency >= 15:
            return "Moderately Efficient"
        elif efficiency >= 5:
            return "Inefficient"
        else:
            return "Highly Inefficient"
    
    def _calculate_trend(self, data: Dict[str, Any]) -> str:
        """Calculate performance trend based on recent data."""
        # Simple trend calculation based on quality score
        quality_score = float(data.get('quality_score', 0))
        
        if quality_score >= 70:
            return "Improving"
        elif quality_score >= 50:
            return "Stable"
        elif quality_score >= 30:
            return "Declining"
        else:
            return "Critical"
    
    def _get_optimization_priority(self, efficiency: float, waste_ratio: float) -> str:
        """Determine optimization priority."""
        if efficiency < 5 or waste_ratio > 80:
            return "Critical"
        elif efficiency < 15 or waste_ratio > 50:
            return "High"
        elif efficiency < 30 or waste_ratio > 30:
            return "Medium"
        else:
            return "Low"
    
    def _analyze_fetch_costs(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze runtime costs of fetching."""
        cost_analysis = {}
        
        for source_name, data in source_data.items():
            # Calculate cost metrics
            total_jobs = int(data.get('total_fetched', 0))
            pm_jobs = int(data.get('pm_accepted', 0))
            avg_duration = float(data.get('avg_fetch_duration', '0').replace('s', ''))
            
            # Cost per PM job
            cost_per_pm = (total_jobs * avg_duration) / max(pm_jobs, 1)
            
            # Cost efficiency
            cost_efficiency = (pm_jobs / max(total_jobs, 1)) * (100 / max(avg_duration, 1))
            
            # Cost category
            cost_category = self._categorize_cost(cost_per_pm)
            
            cost_analysis[source_name] = {
                'cost_per_pm_job': f"{cost_per_pm:.2f}s",
                'cost_efficiency': f"{cost_efficiency:.1f}",
                'cost_category': cost_category,
                'total_runtime_cost': f"{total_jobs * avg_duration:.1f}s",
                'pm_job_cost_ratio': f"{(pm_jobs / max(total_jobs, 1)) * 100:.1f}%"
            }
        
        return cost_analysis
    
    def _categorize_cost(self, cost_per_pm: float) -> str:
        """Categorize cost efficiency."""
        if cost_per_pm <= 10:
            return "Very Low Cost"
        elif cost_per_pm <= 20:
            return "Low Cost"
        elif cost_per_pm <= 40:
            return "Medium Cost"
        elif cost_per_pm <= 80:
            return "High Cost"
        else:
            return "Very High Cost"
    
    def _identify_optimization_opportunities(self, source_data: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []
        
        # Analyze patterns across sources
        low_efficiency_sources = [
            name for name, data in source_data.items()
            if float(data.get('pm_accepted', 0)) / max(int(data.get('total_fetched', 1)), 1) < 0.1
        ]
        
        high_waste_sources = [
            name for name, data in source_data.items()
            if int(data.get('pm_rejected', 0)) / max(int(data.get('total_fetched', 1)), 1) > 0.7
        ]
        
        slow_sources = [
            name for name, data in source_data.items()
            if float(data.get('avg_fetch_duration', '0').replace('s', '')) > 60
        ]
        
        # Generate specific recommendations
        if low_efficiency_sources:
            opportunities.append(
                f"Optimize low-efficiency sources: {', '.join(low_efficiency_sources)} "
                f"(efficiency < 10%)"
            )
        
        if high_waste_sources:
            opportunities.append(
                f"Reduce waste in high-rejection sources: {', '.join(high_waste_sources)} "
                f"(waste ratio > 70%)"
            )
        
        if slow_sources:
            opportunities.append(
                f"Optimize slow sources: {', '.join(slow_sources)} "
                f"(duration > 60s)"
            )
        
        # General optimization opportunities
        total_sources = len(source_data)
        if total_sources > 5:
            opportunities.append("Consider source consolidation - too many sources")
        
        avg_efficiency = sum(
            float(data.get('pm_accepted', 0)) / max(int(data.get('total_fetched', 1)), 1)
            for data in source_data.values()
        ) / total_sources if total_sources > 0 else 0
        
        if avg_efficiency < 20:
            opportunities.append("Review overall pre-filtering strategy - low efficiency")
        
        if not opportunities:
            opportunities.append("System operating efficiently")
        
        return opportunities
    
    def _get_efficiency_grade(self, efficiency: float) -> str:
        """Grade fetch efficiency."""
        if efficiency >= 50:
            return "A+"
        elif efficiency >= 40:
            return "A"
        elif efficiency >= 30:
            return "B"
        elif efficiency >= 20:
            return "C"
        else:
            return "D"
