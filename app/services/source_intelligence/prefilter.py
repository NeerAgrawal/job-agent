"""Pre-filtering system for PM role validation before processing."""

from typing import List, Dict, Any

from app.core.logging import logger
from app.services.ai.title_filters import get_title_category


class PMRolePreFilter:
    """Early rejection system for non-target roles.

    Delegates all title classification to the single source of truth in
    ``app.services.ai.title_filters`` so the accepted/rejected role definitions
    stay consistent with the scorer and the rest of the pipeline (previously this
    class kept its own hardcoded lists that drifted out of sync -- e.g. it
    early-accepted senior/principal PM roles the target profile should reject).
    """

    def __init__(self):
        self.logger = logger.bind(service="prefilter")

    @staticmethod
    def _title_of(job: Any) -> str:
        if hasattr(job, 'title'):
            return job.title or ""
        return job.get('title', '') if isinstance(job, dict) else ""

    def prefilter_jobs(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Filter jobs before expensive processing.

        Only titles classified as target product roles ("pm") are accepted;
        everything else (explicit rejects and unknown/ambiguous titles) is
        rejected, since ambiguous non-product titles are not worth scoring.
        """
        if not jobs:
            return {
                'accepted': [],
                'rejected': [],
                'stats': {
                    'total_input': 0,
                    'early_accepted': 0,
                    'early_rejected': 0,
                    'rejection_rate': 0.0,
                    'pm_density': 0.0,
                    'rejection_reasons': {},
                }
            }

        accepted = []
        rejected = []
        rejection_reasons: Dict[str, int] = {}

        for job in jobs:
            title = self._title_of(job)
            category = get_title_category(title)

            if category == "pm":
                accepted.append(job)
            else:
                rejected.append(job)
                reason = "empty_title" if not title.strip() else f"non_target_role_{category}"
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

        total = len(jobs)
        early_accepted = len(accepted)
        early_rejected = len(rejected)
        rejection_rate = (early_rejected / total) * 100 if total > 0 else 0
        pm_density = (early_accepted / total) * 100 if total > 0 else 0

        stats = {
            'total_input': total,
            'early_accepted': early_accepted,
            'early_rejected': early_rejected,
            'rejection_rate': rejection_rate,
            'pm_density': pm_density,
            'rejection_reasons': rejection_reasons,
        }

        self.logger.info(
            f"Pre-filter: {total} -> {early_accepted} accepted, "
            f"{early_rejected} rejected ({rejection_rate:.1f}% rejection, "
            f"{pm_density:.1f}% PM density)"
        )

        return {
            'accepted': accepted,
            'rejected': rejected,
            'stats': stats,
        }

    def get_rejection_summary(self, stats: Dict[str, Any]) -> str:
        """Get human-readable rejection summary."""
        if not stats.get('rejection_reasons'):
            return "No rejections"

        reasons = stats['rejection_reasons']
        summary_parts = []

        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)

        for reason, count in sorted_reasons[:5]:
            if count > 0:
                readable_reason = reason.replace('_', ' ').title()
                summary_parts.append(f"{readable_reason}: {count}")

        return " | ".join(summary_parts) if summary_parts else "No major rejections"
