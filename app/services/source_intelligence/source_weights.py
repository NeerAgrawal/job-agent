"""Source quality weighting system for PM job sources."""

from typing import Dict, Any
from dataclasses import dataclass

from app.core.logging import logger


@dataclass
class SourceWeight:
    """Weight configuration for a job source."""
    source_name: str
    quality_weight: float
    reliability_weight: float
    freshness_weight: float
    pm_density_weight: float
    
    @property
    def overall_weight(self) -> float:
        """Calculate overall source weight."""
        return (
            self.quality_weight * 0.4 +
            self.reliability_weight * 0.3 +
            self.freshness_weight * 0.2 +
            self.pm_density_weight * 0.1
        )


class SourceWeightManager:
    """Manages source quality weights and scoring bonuses."""
    
    def __init__(self):
        self.logger = logger.bind(service="source_weights")
        
        # Default source weights based on historical performance
        self.source_weights = {
            'greenhouse': SourceWeight(
                source_name='greenhouse',
                quality_weight=0.6,  # Good PM density but noisy
                reliability_weight=0.8,  # Stable API
                freshness_weight=0.7,  # Regular updates
                pm_density_weight=0.5   # Low PM density
            ),
            'lever': SourceWeight(
                source_name='lever',
                quality_weight=1.0,  # Highest PM density
                reliability_weight=0.9,  # Very stable
                freshness_weight=0.8,  # Good updates
                pm_density_weight=1.0   # Best PM density
            ),
            'wellfound': SourceWeight(
                source_name='wellfound',
                quality_weight=0.3,  # Mixed quality
                reliability_weight=0.6,  # Sometimes unstable
                freshness_weight=0.9,  # Very fresh
                pm_density_weight=0.4   # Variable PM density
            ),
            'instahyre': SourceWeight(
                source_name='instahyre',
                quality_weight=0.8,  # Good PM filtering
                reliability_weight=0.7,  # Moderately stable
                freshness_weight=0.6,  # Regular updates
                pm_density_weight=0.8   # Good PM density
            ),
            'cutshort': SourceWeight(
                source_name='cutshort',
                quality_weight=0.75,  # Good quality
                reliability_weight=0.75,  # Stable
                freshness_weight=0.7,  # Regular updates
                pm_density_weight=0.75  # Good PM density
            ),
            'naukri': SourceWeight(
                source_name='naukri',
                quality_weight=0.7,  # Moderate quality
                reliability_weight=0.8,  # Stable
                freshness_weight=0.8,  # Very fresh
                pm_density_weight=0.6   # Moderate PM density
            ),
        }
    
    def _normalize_source_name(self, source_name: str) -> str:
        """Normalize a source name for weight lookup (case-insensitive, strips browser-fallback suffix)."""
        normalized = (source_name or "").strip().lower()
        if normalized.endswith("_browser"):
            normalized = normalized[: -len("_browser")]
        return normalized

    def get_source_weight(self, source_name: str) -> float:
        """Get overall weight for a source."""
        normalized = self._normalize_source_name(source_name)

        if normalized not in self.source_weights:
            self.logger.warning(f"Unknown source: {source_name}, using default weight 0.5")
            return 0.5

        weight = self.source_weights[normalized].overall_weight
        self.logger.debug(f"Source {source_name} weight: {weight:.2f}")
        return weight
    
    def get_source_bonus(self, source_name: str, base_score: float) -> float:
        """Calculate source quality bonus for scoring."""
        source_weight = self.get_source_weight(source_name)
        
        # Bonus is weight * 5 (max 5 points)
        bonus = source_weight * 5.0
        
        self.logger.debug(
            f"Source bonus for {source_name}: {bonus:.2f} "
            f"(weight: {source_weight:.2f}, base_score: {base_score:.1f})"
        )
        
        return bonus
    
    def update_source_weight(self, source_name: str, metric_updates: Dict[str, float]) -> None:
        """Update source weights based on performance metrics."""
        normalized = self._normalize_source_name(source_name)

        if normalized not in self.source_weights:
            self.logger.warning(f"Cannot update unknown source: {source_name}")
            return

        current_weight = self.source_weights[normalized]
        
        # Update weights based on performance
        if 'pm_density' in metric_updates:
            density_score = metric_updates['pm_density']
            current_weight.pm_density_weight = min(density_score / 100, 1.0)
        
        if 'reliability' in metric_updates:
            reliability_score = metric_updates['reliability']
            current_weight.reliability_weight = min(reliability_score, 1.0)
        
        if 'freshness' in metric_updates:
            freshness_score = metric_updates['freshness']
            current_weight.freshness_weight = min(freshness_score, 1.0)
        
        # Recalculate quality weight based on performance
        if 'quality_score' in metric_updates:
            quality_score = metric_updates['quality_score']
            current_weight.quality_weight = min(quality_score / 100, 1.0)
        
        self.logger.info(
            f"Updated weights for {source_name}: "
            f"quality={current_weight.quality_weight:.2f}, "
            f"reliability={current_weight.reliability_weight:.2f}, "
            f"freshness={current_weight.freshness_weight:.2f}, "
            f"density={current_weight.pm_density_weight:.2f}"
        )
    
    def get_weighted_sources(self) -> Dict[str, float]:
        """Get all sources sorted by weight."""
        return {
            name: weight.overall_weight
            for name, weight in self.source_weights.items()
        }
    
    def get_top_sources(self, limit: int = 3) -> list:
        """Get top-weighted sources."""
        sorted_sources = sorted(
            self.source_weights.items(),
            key=lambda x: x[1].overall_weight,
            reverse=True
        )
        
        return [
            {
                'source_name': name,
                'weight': weight.overall_weight,
                'components': {
                    'quality': weight.quality_weight,
                    'reliability': weight.reliability_weight,
                    'freshness': weight.freshness_weight,
                    'pm_density': weight.pm_density_weight
                }
            }
            for name, weight in sorted_sources[:limit]
        ]
    
    def get_source_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of source weights."""
        return {
            'total_sources': len(self.source_weights),
            'average_weight': sum(w.overall_weight for w in self.source_weights.values()) / len(self.source_weights),
            'top_sources': self.get_top_sources(),
            'source_details': {
                name: {
                    'overall_weight': weight.overall_weight,
                    'quality_weight': weight.quality_weight,
                    'reliability_weight': weight.reliability_weight,
                    'freshness_weight': weight.freshness_weight,
                    'pm_density_weight': weight.pm_density_weight
                }
                for name, weight in self.source_weights.items()
            }
        }
