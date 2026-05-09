"""Pre-filtering system for PM role validation before processing."""

from typing import List, Dict, Any
import re

from app.core.logging import logger


class PMRolePreFilter:
    """Early rejection system for obvious non-PM roles."""
    
    def __init__(self):
        self.logger = logger.bind(service="prefilter")
        
        # Early reject roles (obvious non-PM)
        self.early_reject_roles = {
            # Sales roles
            'account executive', 'sales', 'business development', 'business development manager',
            'sales manager', 'sales representative', 'business development executive',
            
            # Engineering roles
            'backend engineer', 'frontend engineer', 'full stack engineer', 'software engineer',
            'android engineer', 'ios engineer', 'mobile engineer', 'devops engineer',
            'qa engineer', 'test engineer', 'quality assurance', 'quality engineer',
            
            # Marketing roles
            'marketing', 'marketing manager', 'digital marketing', 'content marketing',
            'growth marketer', 'product marketing', 'brand manager',
            
            # Support roles
            'customer success', 'customer support', 'technical support', 'support engineer',
            'customer service', 'client success', 'account manager',
            
            # Analyst roles
            'data analyst', 'business analyst', 'systems analyst', 'financial analyst',
            'market research analyst', 'operations analyst', 'product analyst',
            
            # Recruiter roles
            'recruiter', 'talent acquisition', 'hr', 'human resources',
            'talent scout', 'recruiting coordinator',
            
            # Operations roles
            'operations', 'operations manager', 'site reliability engineer',
            'platform engineer', 'infrastructure engineer', 'devops',
            
            # Designer roles
            'ux designer', 'ui designer', 'product designer', 'graphic designer',
            'visual designer', 'interaction designer',
        }
        
        # Early accept roles (obvious PM)
        self.early_accept_roles = {
            'product manager', 'pm', 'associate product manager', 'apm',
            'technical product manager', 'tpm', 'senior product manager', 'spm',
            'principal product manager', 'group product manager', 'gpm',
            'ai product manager', 'platform product manager', 'growth product manager',
            'product owner', 'product lead', 'head of product', 'vp product',
        }
    
    def prefilter_jobs(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Filter jobs before expensive processing."""
        if not jobs:
            return {
                'accepted': [],
                'rejected': [],
                'stats': {
                    'total_input': 0,
                    'early_accepted': 0,
                    'early_rejected': 0,
                    'rejection_rate': 0.0,
                    'pm_density': 0.0
                }
            }
        
        accepted = []
        rejected = []
        rejection_reasons = {}
        
        for job in jobs:
            title = job.get('title', '').lower().strip()
            
            # Clean title for better matching
            cleaned_title = self._clean_title(title)
            
            # Early rejection check
            should_reject, reason = self._should_early_reject(cleaned_title)
            
            if should_reject:
                rejected.append(job)
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
            else:
                accepted.append(job)
        
        # Calculate statistics
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
            'rejection_reasons': rejection_reasons
        }
        
        self.logger.info(
            f"Pre-filter: {total} → {early_accepted} accepted, "
            f"{early_rejected} rejected ({rejection_rate:.1f}% rejection, "
            f"{pm_density:.1f}% PM density)"
        )
        
        return {
            'accepted': accepted,
            'rejected': rejected,
            'stats': stats
        }
    
    def _clean_title(self, title: str) -> str:
        """Clean job title for better matching."""
        if not title:
            return ""
        
        # Remove common noise words
        noise_words = [
            'senior', 'junior', 'lead', 'principal', 'staff', 'associate',
            'manager', 'director', 'vp', 'head', 'chief', 'executive',
            'remote', 'hybrid', 'onsite', 'wfh', 'work from home'
        ]
        
        cleaned = title.lower()
        
        # Remove noise words (keep PM variations)
        for word in noise_words:
            if word not in ['pm', 'product manager', 'associate product manager']:
                cleaned = cleaned.replace(f" {word} ", " ").replace(f" {word}", "")
        
        # Normalize spacing
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _should_early_reject(self, title: str) -> tuple[bool, str]:
        """Determine if job should be early rejected."""
        if not title:
            return True, "empty_title"
        
        # Check for early accept roles
        for accept_role in self.early_accept_roles:
            if accept_role in title:
                return False, ""
        
        # Check for early reject roles
        for reject_role in self.early_reject_roles:
            if reject_role in title:
                return True, f"non_pm_role_{reject_role.replace(' ', '_')}"
        
        # Check for mixed titles (PM + non-PM)
        mixed_patterns = [
            (r'product manager.*sales', 'pm_sales_mix'),
            (r'sales.*product manager', 'sales_pm_mix'),
            (r'product manager.*marketing', 'pm_marketing_mix'),
            (r'marketing.*product manager', 'marketing_pm_mix'),
        ]
        
        for pattern, reason in mixed_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True, reason
        
        # Check for intern roles (unless PM intern)
        if 'intern' in title and 'product manager' not in title:
            return True, "non_pm_intern"
        
        # Check for contractor/freelance (unless PM)
        if ('contractor' in title or 'freelance' in title) and 'product manager' not in title:
            return True, "non_pm_contractor"
        
        return False, ""
    
    def get_rejection_summary(self, stats: Dict[str, Any]) -> str:
        """Get human-readable rejection summary."""
        if not stats.get('rejection_reasons'):
            return "No rejections"
        
        reasons = stats['rejection_reasons']
        summary_parts = []
        
        # Top rejection reasons
        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
        
        for reason, count in sorted_reasons[:5]:
            if count > 0:
                readable_reason = reason.replace('_', ' ').title()
                summary_parts.append(f"{readable_reason}: {count}")
        
        return " | ".join(summary_parts) if summary_parts else "No major rejections"
