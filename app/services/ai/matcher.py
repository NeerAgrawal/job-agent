"""Semantic matching engine for job-resume compatibility."""

import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.ai.embeddings import EmbeddingsEngine
from app.core.logging import logger
from .title_filters import is_pm_role, is_reject_role, is_transition_friendly


@dataclass
class JobMatch:
    """Job match result."""
    job_id: str
    job_title: str
    company: str
    similarity_score: float
    relevance_reason: str
    transition_friendly: bool = False


class MatchingEngine:
    """Semantic matching engine for jobs and resumes."""
    
    def __init__(self, embeddings_engine: EmbeddingsEngine):
        self.logger = logger.bind(service="matching_engine")
        self.embeddings_engine = embeddings_engine
        
    async def find_matches(
        self,
        resume_embedding: np.ndarray,
        job_embeddings: List[np.ndarray],
        job_data: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[JobMatch]:
        """Find top matching jobs for a resume."""
        try:
            self.logger.info(f"Finding matches for {len(job_embeddings)} jobs")
            
            if not job_embeddings or len(job_embeddings) == 0:
                self.logger.warning("No job embeddings provided")
                return []
            
            # Calculate similarities
            similarities = await self._calculate_similarities(
                resume_embedding, 
                job_embeddings
            )
            
            # Create job matches with metadata
            matches = []
            for i, similarity in enumerate(similarities):
                if i < len(job_data):
                    job = job_data[i]
                    match = JobMatch(
                        job_id=str(job.id),
                        job_title=job.title,
                        company=job.company,
                        similarity_score=float(similarity),
                        relevance_reason=self._generate_relevance_reason(similarity, job)
                    )
                    
                    # Add transition-friendly flag
                    if is_transition_friendly(job.title):
                        match.transition_friendly = True
                    
                    matches.append(match)
            
            # Sort with transition-friendly priority
            transition_friendly_matches = [m for m in matches if hasattr(m, 'transition_friendly')]
            other_pm_matches = [m for m in matches if not hasattr(m, 'transition_friendly')]
            
            # Sort each group by similarity score (descending)
            transition_friendly_sorted = sorted(transition_friendly_matches, key=lambda x: x.similarity_score, reverse=True)
            other_pm_sorted = sorted(other_pm_matches, key=lambda x: x.similarity_score, reverse=True)
            
            # Combine: transition-friendly first, then other PM roles
            final_matches = transition_friendly_sorted + other_pm_sorted
            
            # Return top matches
            top_matches = final_matches[:top_k]
            
            self.logger.info(f"Found {len(top_matches)} top matches ({len(transition_friendly_sorted)} transition-friendly)")
            return top_matches
            
        except Exception as e:
            self.logger.exception("Failed to find job matches")
            return []
    
    async def _calculate_similarities(
        self,
        resume_embedding: np.ndarray,
        job_embeddings: List[np.ndarray]
    ) -> List[float]:
        """Calculate cosine similarities between resume and jobs."""
        try:
            similarities = []
            
            for job_embedding in job_embeddings:
                similarity = await self.embeddings_engine.cosine_similarity(
                    resume_embedding, 
                    job_embedding
                )
                similarities.append(similarity)
            
            return similarities
            
        except Exception as e:
            self.logger.exception("Failed to calculate similarities")
            return []
    
    def _generate_relevance_reason(self, similarity_score: float, job) -> str:
        """Generate human-readable relevance reason."""
        reasons = []
        
        # High similarity
        if similarity_score >= 0.8:
            reasons.append("Strong semantic match")
        
        # PM role alignment
        title = job.title.lower()
        pm_keywords = ["product manager", "program manager", "project manager", "pm"]
        if any(keyword in title for keyword in pm_keywords):
            reasons.append("PM role alignment")
        
        # Technical skills alignment
        description = job.jd_text.lower()
        tech_keywords = ["python", "javascript", "api", "database", "cloud", "aws"]
        if any(keyword in description for keyword in tech_keywords):
            reasons.append("Technical skills match")
        
        # Experience level match
        if "senior" in title or "lead" in title:
            reasons.append("Senior level position")
        
        if not reasons:
            return "Moderate match"
        
        return ", ".join(reasons)
    
    async def match_jobs_to_resume(
        self,
        resume_text: str,
        jobs: List[Any],
        top_k: int = 10
    ) -> List[JobMatch]:
        """Match jobs to resume using semantic similarity."""
        try:
            self.logger.info(f"Matching {len(jobs)} jobs to resume")
            
            # Filter to PM roles with transition awareness
            pm_jobs = []
            non_pm_jobs = []
            transition_friendly_jobs = []
        
            for job in jobs:
                if is_pm_role(job.title):
                    if is_transition_friendly(job.title):
                        transition_friendly_jobs.append(job)
                    else:
                        pm_jobs.append(job)
                elif is_reject_role(job.title):
                    non_pm_jobs.append(job)
                else:
                    # Edge case - treat as non-PM for safety
                    non_pm_jobs.append(job)
            
            self.logger.info(f"Filtered to {len(pm_jobs)} PM jobs, {len(transition_friendly_jobs)} transition-friendly jobs, and {len(non_pm_jobs)} non-PM jobs")
            
            if not pm_jobs and not transition_friendly_jobs:
                self.logger.warning("No PM-relevant jobs found after filtering")
                return []
            
            # Generate resume embedding
            resume_embedding = await self.embeddings_engine.embed_resume(resume_text)
            if resume_embedding is None:
                self.logger.error("Failed to generate resume embedding")
                return []
            
            # Generate job embeddings
            job_texts = [job.jd_text for job in pm_jobs]
            job_embeddings = await self.embeddings_engine.embed_jobs_batch(job_texts)
            
            if not job_embeddings:
                self.logger.error("Failed to generate job embeddings")
                return []
            
            # Find matches
            matches = await self.find_matches(
                resume_embedding,
                job_embeddings,
                pm_jobs,
                top_k
            )
            
            # Sort by similarity score
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Return top matches
            top_matches = matches[:top_k]
            
            self.logger.info(f"Successfully matched {len(top_matches)} PM jobs")
            return top_matches
            
        except Exception as e:
            self.logger.exception("Failed to match jobs to resume")
            return []
    
    async def semantic_search(
        self,
        query: str,
        job_embeddings: List[np.ndarray],
        job_data: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[JobMatch]:
        """Semantic search within job embeddings."""
        try:
            self.logger.info(f"Performing semantic search: {query}")
            
            # Generate query embedding
            query_embedding = await self.embeddings_engine.embed_resume(query)
            if query_embedding is None:
                return []
            
            # Calculate similarities
            similarities = await self._calculate_similarities(
                query_embedding,
                job_embeddings
            )
            
            # Create search results
            results = []
            for i, similarity in enumerate(similarities):
                if i < len(job_data):
                    job = job_data[i]
                    result = JobMatch(
                        job_id=str(job.id),
                        job_title=job.title,
                        company=job.company,
                        similarity_score=float(similarity),
                        relevance_reason=f"Semantic similarity: {similarity:.2f}"
                    )
                    results.append(result)
            
            # Sort by similarity
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            self.logger.exception("Failed semantic search")
            return []
