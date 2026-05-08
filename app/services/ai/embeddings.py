"""Embeddings engine for semantic job matching."""

import asyncio
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from app.core.logging import logger


class EmbeddingsEngine:
    """Local embeddings engine using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.logger = logger.bind(service="embeddings")
        self.model_name = model_name
        self.model = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        
    async def initialize(self) -> None:
        """Initialize the embeddings model."""
        try:
            self.logger.info(f"Loading embeddings model: {self.model_name}")
            
            # Load model locally
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self._device)
            
            self.logger.info(f"Embeddings model loaded on device: {self._device}")
            
        except Exception as e:
            self.logger.exception("Failed to load embeddings model")
            raise
    
    async def embed_resume(self, resume_text: str) -> Optional[np.ndarray]:
        """Generate embedding for resume text."""
        try:
            if not self.model:
                await self.initialize()
            
            self.logger.debug("Generating resume embedding")
            
            # Chunk text for better embeddings
            chunks = self._chunk_text(resume_text)
            embeddings = []
            
            for chunk in chunks:
                embedding = self.model.encode(
                    chunk,
                    convert_to_tensor=True,
                    show_progress_bar=False
                )
                embeddings.append(embedding.cpu().numpy())
            
            # Average embeddings for resume representation
            resume_embedding = np.mean(embeddings, axis=0)
            
            self.logger.debug("Resume embedding generated successfully")
            return resume_embedding
            
        except Exception as e:
            self.logger.exception("Failed to embed resume")
            return None
    
    async def embed_job(self, job_text: str) -> Optional[np.ndarray]:
        """Generate embedding for job description."""
        try:
            if not self.model:
                await self.initialize()
            
            self.logger.debug("Generating job embedding")
            
            # Job descriptions are shorter, no chunking needed
            embedding = self.model.encode(
                job_text,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            
            job_embedding = embedding.cpu().numpy()
            
            self.logger.debug("Job embedding generated successfully")
            return job_embedding
            
        except Exception as e:
            self.logger.exception("Failed to embed job")
            return None
    
    async def embed_jobs_batch(self, job_texts: List[str]) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple jobs in batch."""
        try:
            if not self.model:
                await self.initialize()
            
            self.logger.info(f"Generating embeddings for {len(job_texts)} jobs")
            
            # Batch process for efficiency
            embeddings = self.model.encode(
                job_texts,
                convert_to_tensor=True,
                show_progress_bar=False,
                batch_size=8
            )
            
            # Convert to numpy arrays
            job_embeddings = [emb.cpu().numpy() for emb in embeddings]
            
            self.logger.info(f"Batch embeddings generated for {len(job_embeddings)} jobs")
            return job_embeddings
            
        except Exception as e:
            self.logger.exception("Failed to generate batch embeddings")
            return []
    
    async def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Normalize embeddings
            norm1 = embedding1 / np.linalg.norm(embedding1)
            norm2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(norm1, norm2)
            
            return float(similarity)
            
        except Exception as e:
            self.logger.exception("Failed to calculate cosine similarity")
            return 0.0
    
    def _chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """Split text into chunks for processing."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        try:
            if not self.model:
                return {"error": "Model not loaded"}
            
            return {
                "model_name": self.model_name,
                "device": self._device,
                "embedding_dim": self.model.get_sentence_embedding_dimension(),
                "max_seq_length": getattr(self.model, 'max_seq_length', 512)
            }
            
        except Exception as e:
            self.logger.exception("Failed to get model info")
            return {"error": str(e)}
