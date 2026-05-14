#!/usr/bin/env python3
"""AI matching test script."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.ai.resume_parser import ResumeParser
from app.services.ai.profile_builder import ProfileBuilder
from app.services.ai.embeddings import EmbeddingsEngine
from app.services.ai.matcher import MatchingEngine
from app.services.ai.scorer import ScoringEngine
from app.database.session import get_db_session
from app.repositories.job import JobRepository
from app.core.logging import setup_logging, logger


async def test_ai_matching():
    """Comprehensive AI matching test."""
    setup_logging()
    
    try:
        print("🤖 Starting AI Matching Test")
        print("=" * 50)
        
        # Test 1: Resume parsing
        print("\n📄 Testing Resume Parser...")
        resume_text = """
        John Doe
        Senior Product Manager
        TechCorp Inc.
        
        Experience:
        - 8 years as Product Manager
        - 5 years as Program Manager
        - Led teams of 5-10 engineers
        - Managed $2M annual budget
        - Launched 3 products from concept to market
        
        Skills:
        - Python, JavaScript, React, AWS, Docker
        - Agile, Scrum, Jira, Confluence
        - REST APIs, Microservices, GraphQL
        - Product roadmapping, KPI tracking
        
        Education:
        - MBA in Product Management
        - Bachelor's in Computer Science
        
        Projects:
        - E-commerce platform (React, Node.js, PostgreSQL)
        - API gateway (Python, FastAPI, AWS)
        - Analytics dashboard (Python, Pandas, D3.js)
        
        Tools:
        - GitHub, GitLab, CI/CD, Jenkins
        - AWS, GCP, Azure
        - Jira, Confluence, Slack, Teams
        - Docker, Kubernetes, Terraform
        """
        
        parser = ResumeParser()
        # Parse resume text directly (no file needed)
        resume_data = parser._extract_resume_data(resume_text)
        
        if resume_data:
            print(f"   ✅ Resume parsed successfully")
            print(f"   Skills found: {len(resume_data.get('skills', []))}")
            print(f"   PM keywords: {len(resume_data.get('pm_keywords', []))}")
            print(f"   Years experience: {resume_data.get('years_experience', 'N/A')}")
            print(f"   Technical strength: {resume_data.get('technical_strength', 'N/A')}")
        else:
            print("   ❌ Resume parsing failed")
            return
        
        # Test 2: Profile building
        print("\n👤 Testing Profile Builder...")
        builder = ProfileBuilder()
        profile = await builder.build_profile(resume_data)
        
        if profile:
            print(f"   ✅ Profile built successfully")
            print(f"   Target roles: {profile.target_roles}")
            print(f"   Technical strength: {profile.technical_strength}")
            print(f"   PM transition score: {profile.pm_transition_score:.1f}")
        else:
            print("   ❌ Profile building failed")
            return
        
        # Test 3: Embeddings engine
        print("\n🧠 Testing Embeddings Engine...")
        embeddings_engine = EmbeddingsEngine()
        await embeddings_engine.initialize()
        
        model_info = await embeddings_engine.get_model_info()
        print(f"   ✅ Model loaded: {model_info.get('model_name', 'unknown')}")
        print(f"   Device: {model_info.get('device', 'unknown')}")
        print(f"   Embedding dim: {model_info.get('embedding_dim', 'unknown')}")
        
        # Test embedding generation
        resume_embedding = await embeddings_engine.embed_resume(resume_text)
        if resume_embedding is not None:
            print(f"   ✅ Resume embedding generated: {resume_embedding.shape}")
        else:
            print("   ❌ Resume embedding failed")
            return
        
        # Test 4: Load jobs from database
        print("\n💾 Loading Jobs from Database...")
        async with get_db_session() as session:
            job_repo = JobRepository(session)
            jobs = await job_repo.get_recent_jobs(days=30, limit=20)
            
            print(f"   ✅ Loaded {len(jobs)} jobs from database")
            
            if not jobs:
                print("   ⚠️  No jobs found in database")
                return
        
        # Test 5: Matching engine
        print("\n🎯 Testing Matching Engine...")
        matcher = MatchingEngine(embeddings_engine)
        
        # Generate job embeddings
        job_texts = [job.jd_text for job in jobs]
        job_embeddings = await embeddings_engine.embed_jobs_batch(job_texts)
        
        if not job_embeddings:
            print("   ❌ Failed to generate job embeddings")
            return
        
        # Find matches
        matches = await matcher.match_jobs_to_resume(
            resume_text,
            jobs,
            top_k=10
        )
        
        print(f"   ✅ Found {len(matches)} job matches")
        
        # Test 6: Scoring engine
        print("\n📊 Testing Scoring Engine...")
        scorer = ScoringEngine()
        
        # Score top matches
        scored_jobs = []
        async with get_db_session() as session:
            job_repo = JobRepository(session)
            
            for i, match in enumerate(matches[:5]):
                # Find the corresponding Job object
                job_obj = next((job for job in jobs if job.title == match.job_title and job.company == match.company), None)
                
                if job_obj:
                    score = await scorer.score_job(
                        job_obj,
                        resume_data,
                        match.similarity_score
                    )
                    
                    if score:  # Only process if score meets quality threshold
                        # Persist scores to database
                        scores_dict = {
                            "semantic": score.semantic_score,
                            "final": score.final_score,
                            "salary": score.salary_score,
                            "transition": score.qa_to_pm_score
                        }
                        
                        await job_repo.update_ai_scores(
                            job_obj.id,
                            scores_dict,
                            score.relevance_reason
                        )
                        
                        scored_jobs.append((match, score))
                        
                        print(f"   Job {i+1}: {match.job_title} at {match.company}")
                        print(f"      Semantic: {score.semantic_score:.1f}")
                        print(f"      PM Role: {score.pm_role_score:.1f}")
                        print(f"      QA->PM: {score.qa_to_pm_score:.1f}")
                        print(f"      API: {score.api_platform_score:.1f}")
                        print(f"      AI/Tech: {score.ai_technical_score:.1f}")
                        print(f"      Salary: {score.salary_score:.1f}")
                        print(f"      Recency: {score.recency_score:.1f}")
                        print(f"      Location: {score.location_score:.1f}")
                        print(f"      Final: {score.final_score:.1f}")
                        print(f"      Reason: {score.relevance_reason}")
                        print(f"      ✅ Scores persisted to database")
                    else:
                        print(f"   Job {i+1}: {match.job_title} at {match.company}")
                        print(f"      ❌ Score below quality threshold ({scorer.minimum_quality_score})")
        
        # Test 7: Results summary
        print("\n📈 Results Summary:")
        print(f"   Total jobs processed: {len(jobs)}")
        print(f"   Matches found: {len(matches)}")
        print(f"   Jobs scored: {len(scored_jobs)}")
        
        # Calculate statistics
        avg_score = sum(score.final_score for _, score in scored_jobs) / len(scored_jobs) if scored_jobs else 0
        high_scoring_jobs = len([job for _, score in scored_jobs if score.final_score >= 70])
        
        print(f"   Average final score: {avg_score:.1f}")
        print(f"   High-scoring jobs (70+): {high_scoring_jobs}")
        
        print("\n" + "=" * 50)
        print("✅ AI Matching Test Completed Successfully!")
        
        return True
        
    except Exception as e:
        logger.exception("AI matching test failed")
        print(f"\n❌ Test failed: {e}")
        return False


def main():
    """Main function for AI matching test."""
    try:
        success = asyncio.run(test_ai_matching())
        if success:
            print("\n✅ All AI matching tests passed!")
            sys.exit(0)
        else:
            print("\n❌ AI matching tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
