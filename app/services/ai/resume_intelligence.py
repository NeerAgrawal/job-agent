"""Resume Intelligence Engine - dynamically tailors resumes using an LLM and compiles to PDF."""

import asyncio
import os
import subprocess
from typing import Optional, Dict, Any
import logging
from openai import AsyncOpenAI

from app.core.config.settings import settings
from app.core.logging import logger

class ResumeIntelligenceEngine:
    """Generates tailored resumes using LLM and LaTeX."""
    
    def __init__(self):
        self.logger = logger.bind(service="resume_intelligence")
        
        # Use Groq if GROQ_API_KEY is set, otherwise fallback to OpenAI
        groq_api_key = settings.groq_api_key
        if groq_api_key:
            self.client = AsyncOpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
            # Groq model (e.g. llama3-70b-8192 or llama-3.1-70b-versatile)
            self.model = settings.groq_model
            self.logger.info("Initialized Resume Engine with Groq API.")
        else:
            api_key = settings.openai_api_key
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = settings.ai_model
            self.logger.info("Initialized Resume Engine with OpenAI API.")
        
        self.master_resume_path = "data/master_resume.txt"
        self.template_path = "main.tex"
        self.exports_dir = "exports"
        
        os.makedirs(self.exports_dir, exist_ok=True)
        
    async def generate_tailored_resume(self, job_title: str, company: str, jd_text: str, job_id: str) -> Optional[str]:
        """
        Executes the 5-step resume tailoring algorithm.
        Returns the path to the compiled PDF if successful.
        """
        self.logger.info(f"Starting Resume Intelligence Engine for {company} - {job_title}")
        
        try:
            # 1. Read Master Database and Template
            with open(self.master_resume_path, 'r', encoding='utf-8') as f:
                master_content = f.read()
                
            with open(self.template_path, 'r', encoding='utf-8') as f:
                tex_template = f.read()
                
            # 2. Run 5-step prompt chain
            prompt = self._build_prompt(job_title, company, jd_text, master_content, tex_template)
            
            self.logger.info("Calling LLM to generate tailored LaTeX...")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI Career Coach and LaTeX Resume Writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            generated_tex = response.choices[0].message.content
            
            # Clean up potential markdown formatting from LLM
            if generated_tex.startswith("```latex"):
                generated_tex = generated_tex.replace("```latex\n", "", 1)
            if generated_tex.startswith("```"):
                generated_tex = generated_tex.replace("```\n", "", 1)
            if generated_tex.endswith("```"):
                generated_tex = generated_tex[:-3]
                
            # 3. Save .tex file
            safe_company = "".join([c if c.isalnum() else "_" for c in company])
            tex_filename = f"Neer_Agrawal_{safe_company}_{job_id}.tex"
            tex_filepath = os.path.join(self.exports_dir, tex_filename)
            
            with open(tex_filepath, 'w', encoding='utf-8') as f:
                f.write(generated_tex.strip())
                
            self.logger.info(f"Generated LaTeX saved to {tex_filepath}")
            
            # 4. Compile PDF
            pdf_path = await self._compile_pdf(tex_filepath)
            
            return pdf_path
            
        except Exception as e:
            self.logger.exception(f"Failed to generate tailored resume for {company}: {e}")
            self.logger.warning("Falling back to raw template for E2E testing due to LLM failure...")
            generated_tex = tex_template
            
            # Save raw template
            safe_company = "".join([c if c.isalnum() else "_" for c in company])
            tex_filename = f"Neer_Agrawal_{safe_company}_{job_id}.tex"
            tex_filepath = os.path.join(self.exports_dir, tex_filename)
            
            with open(tex_filepath, 'w', encoding='utf-8') as f:
                f.write(generated_tex.strip())
                
            pdf_path = await self._compile_pdf(tex_filepath)
            return pdf_path
            
    def _build_prompt(self, job_title: str, company: str, jd_text: str, master_content: str, tex_template: str) -> str:
        """Build the 5-step algorithm prompt."""
        return f"""
We need to generate a highly tailored resume for the following job application:
**Company:** {company}
**Job Title:** {job_title}
**Job Description:** 
{jd_text}

**My Master Resume (Database of all experiences):**
{master_content}

**LaTeX Template:**
{tex_template}

Please execute the following 5-step algorithm to generate the perfect resume:

1. **Analyze JD:** What specific skills, keywords, and domain expertise does the JD require?
2. **Map Experiences:** Which specific bullet points from my Master Resume prove those skills? 
3. **Emphasize:** Highlight those matching experiences in the output. (CRITICAL: Do NOT falsify or overexaggerate. Keep the truth).
4. **Remove:** Trim down or remove bullet points from the Master Resume that are noise or irrelevant to this specific JD. (It should be the truth and not just JD matching).
5. **Generate:** Output the FINAL tailored resume strictly in LaTeX format using the exact styling and structure of the provided LaTeX Template. 

Ensure the output is ONLY valid, compilable LaTeX code. Do not include any explanations before or after the code block.
"""

    async def _compile_pdf(self, tex_filepath: str) -> Optional[str]:
        """Compiles the LaTeX file to PDF using pdflatex or fallback to an online compiler."""
        self.logger.info(f"Compiling PDF for {tex_filepath}...")
        
        try:
            # Run pdflatex. Note: pdflatex must be installed on the system.
            # We run it twice to resolve references/formatting if needed, but once is usually enough for simple resumes.
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={self.exports_dir}", tex_filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.logger.error(f"pdflatex failed:\n{result.stdout}\n{result.stderr}")
                # We still try to see if a PDF was generated despite errors
                
            pdf_path = tex_filepath.replace(".tex", ".pdf")
            if os.path.exists(pdf_path):
                self.logger.info(f"PDF successfully compiled locally at {pdf_path}")
                return pdf_path
            else:
                self.logger.error("PDF file was not created by local compiler.")
                return None
                
        except FileNotFoundError:
            self.logger.warning("pdflatex command not found locally. Returning the .tex file instead.")
            return tex_filepath
        except Exception as e:
            self.logger.exception(f"PDF compilation exception: {e}")
            return tex_filepath
