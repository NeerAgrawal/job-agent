"""Generate targeted PM resume variants as professional PDFs.

Creates:
1. Neer_Agrawal_AI_PM_Resume.pdf - Optimized for AI/ML Product Manager roles
2. Neer_Agrawal_Technical_PM_Resume.pdf - Optimized for Technical Product Manager roles
3. Neer_Agrawal_Resume.pdf - Updated general PM resume (overwrites existing)
"""

from fpdf import FPDF
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


class ResumePDF(FPDF):
    """Custom PDF class for ATS-friendly, professional resume formatting."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=12)

    def header_section(self, name, contact_line1, contact_line2):
        """Render candidate name and contact info."""
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 8, name, new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, contact_line1, new_x="LMARGIN", new_y="NEXT", align="C")
        self.cell(0, 5, contact_line2, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)
        self.section_line()

    def section_line(self):
        """Draw a thin horizontal separator."""
        self.set_draw_color(60, 60, 60)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def section_heading(self, title):
        """Render a section heading with separator."""
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(25, 25, 112)  # Dark blue
        self.cell(0, 7, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.section_line()

    def subsection_heading(self, title, subtitle="", date_range=""):
        """Render a subsection heading (job title, project name, etc.)."""
        self.set_font("Helvetica", "B", 10)
        
        if date_range:
            # Title on left, date on right
            title_width = self.get_string_width(title) + 4
            self.cell(title_width, 5, title)
            self.set_font("Helvetica", "", 9)
            self.cell(0, 5, date_range, new_x="LMARGIN", new_y="NEXT", align="R")
        else:
            self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        
        if subtitle:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(80, 80, 80)
            self.cell(0, 4, subtitle, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)

    def bullet_point(self, text):
        """Render a bullet point with hanging indent."""
        self.set_font("Helvetica", "", 9)
        indent = self.l_margin + 3
        self.set_x(indent)
        self.cell(4, 4.5, ">")
        self.multi_cell(0, 4.5, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(0.5)

    def skills_section(self, skills_dict):
        """Render skills as Category: items format."""
        for category, items in skills_dict.items():
            self.set_font("Helvetica", "B", 9)
            cat_width = self.get_string_width(category + ": ") + 2
            self.cell(cat_width, 5, category + ": ")
            self.set_font("Helvetica", "", 9)
            self.multi_cell(0, 5, items, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)


# ============================================================================
# CONTACT INFO (shared across all variants)
# ============================================================================
NAME = "NEER AGRAWAL"
CONTACT_LINE1 = "+91 7007027811 | neeragrawal05@gmail.com | Bengaluru, Karnataka"
CONTACT_LINE2 = "linkedin.com/in/neer-agrawal | github.com/NeerAgrawal | portfolio"


# ============================================================================
# 1. AI PM RESUME
# ============================================================================
def generate_ai_pm_resume():
    pdf = ResumePDF()
    pdf.add_page()
    pdf.set_margins(14, 12, 14)
    pdf.header_section(NAME, CONTACT_LINE1, CONTACT_LINE2)

    # --- Professional Summary ---
    pdf.section_heading("Professional Summary")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.multi_cell(0, 5,
        "AI-focused Product Manager with 4.5+ years of experience building and shipping AI/ML products "
        "from 0-to-1. Hands-on experience with LLMs, RAG architectures, and GenAI product pipelines. "
        "Proven ability to translate complex AI capabilities into user-centric product experiences with "
        "measurable business impact. Recognized as Top Fellow at NextLeap PM Fellowship.",
        new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(2)

    # --- Skills ---
    pdf.section_heading("Skills")
    pdf.skills_section({
        "AI & ML Product": "LLM Integration, RAG Systems, Prompt Engineering, AI Agents, GenAI Product Strategy, "
                           "AI-assisted Prototyping, Embedding Models, FAISS Vector Search, Model Evaluation",
        "Product Management": "Product Strategy, Roadmap Planning, PRDs, User Stories, RICE Prioritization, "
                              "MVP Definition, Sprint Planning, GTM Strategy, Customer Journey Mapping",
        "AI Tools & Platforms": "Cursor, Claude Code, Antigravity, Groq LLM, Lovable, n8n Workflow Automation, "
                                "LLM API Integration, Streamlit, FastAPI",
        "Technical": "Python, Java, SQL, REST APIs, Microservices, Async Architecture, Playwright, SQLite",
        "Tools": "Azure DevOps, Git, Postman, PyCharm, Google APIs"
    })

    # --- AI Product Development ---
    pdf.section_heading("AI Product Development")

    pdf.subsection_heading(
        "PM Opportunity Intelligence Platform",
        "Python, Async Architecture, Playwright, AI Automation, Telegram APIs, SQLite"
    )
    pdf.bullet_point(
        "Architected and built a production-grade AI-powered opportunity intelligence platform using async "
        "orchestration and Playwright automation to aggregate, rank, and deliver PM jobs across 4+ platforms."
    )
    pdf.bullet_point(
        "Engineered an AI-powered ATS and resume intelligence engine with automated job deduplication, "
        "resume targeting via LLM scoring, and real-time Telegram delivery - eliminating 10+ hours/week "
        "of manual job hunting."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "NextLeap PM Fellowship Chatbot",
        "RAG, FAISS, Groq LLM, Streamlit"
    )
    pdf.bullet_point(
        "Developed and deployed a RAG-based AI chatbot indexing 13 weeks of curriculum, 18 tools, and "
        "8 instructor profiles using FAISS semantic retrieval + Groq LLM for instant contextual support."
    )
    pdf.bullet_point(
        "Achieved <2 second response time with contextual accuracy, conversation history, and persistent "
        "session memory via Streamlit deployment."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "Gifthesis - AI Gifting Assistant",
        "Groq LLM, Prompt Engineering, AI Workflows"
    )
    pdf.bullet_point(
        "Conducted user research and translated insights into a 3-step AI-driven gifting journey using "
        "Groq LLM and structured prompt engineering, achieving 95%+ recommendation confidence accuracy."
    )
    pdf.bullet_point(
        "Designed and implemented a fallback recommendation engine ensuring 100% uptime and live deployment "
        "reliability."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "Zomato - AI Restaurant Recommendation Engine",
        "FastAPI, Streamlit, LLM Personalization"
    )
    pdf.bullet_point(
        "Engineered a full-stack LLM-powered restaurant recommendation engine processing 1,000+ restaurant "
        "data points with user preference modeling, delivering personalized results in <3 seconds."
    )
    pdf.bullet_point(
        "Architected a complete 6-phase product pipeline from data ingestion to production launch, reducing "
        "build-to-launch time to under 2 weeks."
    )
    pdf.ln(2)

    # --- Product Strategy ---
    pdf.section_heading("Product Strategy & Leadership")

    pdf.subsection_heading(
        "NextLeap PM Fellowship - Top Fellow",
        "",
        "Dec 2025 - Apr 2026"
    )
    pdf.bullet_point(
        "Ranked Top Fellow among 100+ fellows by designing MVP strategy, wireframes, KPI trees, "
        "and GTM prioritization for AI-first product concepts."
    )
    pdf.ln(2)

    # --- Work Experience ---
    pdf.section_heading("Work Experience")

    pdf.subsection_heading(
        "Software Quality Engineer - Infosys",
        "Full-time | Bengaluru, India",
        "Nov 2021 - May 2026"
    )
    pdf.bullet_point(
        "Spearheaded the product lifecycle of an internal Python-based automation framework from ideation "
        "to deployment, driving adoption across QA teams and reducing defect leakage by 20%."
    )
    pdf.bullet_point(
        "Led release strategy and execution across large-scale API & microservices ecosystems, coordinating "
        "with 3+ cross-functional engineering teams to ensure on-time feature delivery."
    )
    pdf.bullet_point(
        "Partnered with Product Owners, developers, and business stakeholders to translate ambiguous "
        "requirements into actionable PRDs, user stories, and acceptance criteria for distributed Agile teams."
    )
    pdf.bullet_point(
        "Optimized CI/CD workflows and automated validation pipelines, reducing retesting effort by 15% "
        "and accelerating deployment readiness for enterprise applications."
    )
    pdf.ln(2)

    # --- Education ---
    pdf.section_heading("Education")
    pdf.subsection_heading(
        "Dayananda Sagar College of Engineering",
        "Bachelor of Engineering (B.E.), Chemical Engineering | Bengaluru, India",
        "2017 - 2021"
    )

    output_path = os.path.join(OUTPUT_DIR, "Neer_Agrawal_AI_PM_Resume.pdf")
    pdf.output(output_path)
    print(f"[OK] AI PM Resume saved: {output_path}")
    return output_path


# ============================================================================
# 2. TECHNICAL PM RESUME
# ============================================================================
def generate_technical_pm_resume():
    pdf = ResumePDF()
    pdf.add_page()
    pdf.set_margins(14, 12, 14)
    pdf.header_section(NAME, CONTACT_LINE1, CONTACT_LINE2)

    # --- Professional Summary ---
    pdf.section_heading("Professional Summary")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.multi_cell(0, 5,
        "Technical Product Manager with 4.5+ years of hands-on software engineering and product delivery "
        "experience. Deep expertise in APIs, microservices, CI/CD pipelines, and automation frameworks. "
        "Proven track record of building developer tools, optimizing engineering workflows, and shipping "
        "production systems at scale. Recognized as Top Fellow at NextLeap PM Fellowship.",
        new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(2)

    # --- Skills ---
    pdf.section_heading("Skills")
    pdf.skills_section({
        "Technical Product": "System Design, API Strategy, Microservices Architecture, CI/CD Pipelines, "
                             "Cloud Infrastructure, DevOps Practices, Automation Frameworks, Database Design",
        "Product Management": "Product Strategy, Roadmap Planning, PRDs, User Stories, RICE Prioritization, "
                              "MVP Definition, Sprint Planning, GTM Strategy, Customer Journey Mapping",
        "Programming & Data": "Python, Java, SQL, REST APIs, FastAPI, Async Architecture, MySQL, SQL Server, "
                              "SQLite, Google APIs",
        "Automation & QA": "Selenium, Robot Framework, Functional Testing, Regression Testing, UAT, "
                           "API Validation, Postman, SoapUI",
        "Tools & DevOps": "Azure DevOps, Git, CI/CD, PyCharm, n8n, Playwright, Docker concepts"
    })

    # --- Work Experience (Lead with Infosys for Technical PM) ---
    pdf.section_heading("Work Experience")

    pdf.subsection_heading(
        "Software Quality Engineer - Infosys",
        "Full-time | Bengaluru, India",
        "Nov 2021 - May 2026"
    )
    pdf.bullet_point(
        "Spearheaded the product lifecycle of an internal Python-based automation framework from ideation "
        "to deployment, driving adoption across QA teams and reducing defect leakage by 20%."
    )
    pdf.bullet_point(
        "Led release strategy and execution across large-scale API & microservices ecosystems for Retail "
        "and Energy domain clients, coordinating with 3+ cross-functional engineering teams to ensure "
        "on-time feature delivery aligned with business goals."
    )
    pdf.bullet_point(
        "Optimized CI/CD workflows and automated validation pipelines, reducing retesting effort by 15% "
        "and accelerating deployment readiness for enterprise applications."
    )
    pdf.bullet_point(
        "Partnered with Product Owners, developers, and business stakeholders to translate ambiguous user "
        "requirements into actionable PRDs, user stories, and acceptance criteria for globally distributed "
        "Agile teams."
    )
    pdf.bullet_point(
        "Took ownership of delivery execution in highly ambiguous environments with limited roadmap clarity, "
        "proactively realigning priorities and ensuring 100% on-time release execution."
    )
    pdf.ln(2)

    # --- Technical Product Development ---
    pdf.section_heading("Technical Product Development")

    pdf.subsection_heading(
        "PM Opportunity Intelligence Platform",
        "Python, Async Architecture, Playwright, Telegram APIs, SQLite"
    )
    pdf.bullet_point(
        "Architected a production-grade platform using async orchestration, Playwright browser automation, "
        "and authenticated scraping workflows to aggregate and rank PM jobs across 4+ platforms (Naukri, "
        "Instahyre, Cutshort, Lever)."
    )
    pdf.bullet_point(
        "Designed and built an automated ATS and resume intelligence engine with job deduplication, resume "
        "targeting, and real-time Telegram delivery - eliminating 10+ hours/week of manual effort."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "Zomato - Restaurant Recommendation Engine",
        "FastAPI, Streamlit, LLM Personalization, Data Pipeline"
    )
    pdf.bullet_point(
        "Engineered a full-stack recommendation engine processing 1,000+ restaurant data points with "
        "LLM-based user preference modeling, delivering personalized results in <3 seconds."
    )
    pdf.bullet_point(
        "Architected a complete 6-phase product pipeline from data ingestion to production launch, "
        "reducing build-to-launch time to under 2 weeks."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "NextLeap PM Fellowship Chatbot",
        "RAG, FAISS Vector DB, Groq LLM, Streamlit"
    )
    pdf.bullet_point(
        "Developed and deployed a RAG-based chatbot with FAISS semantic retrieval indexing 13 weeks of "
        "curriculum content, achieving <2 second response time with conversation history and persistent "
        "session memory."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "Gifthesis - AI Gifting Assistant",
        "Groq LLM, Prompt Engineering, Fallback Architecture"
    )
    pdf.bullet_point(
        "Built an end-to-end AI gifting assistant with structured prompt engineering achieving 95%+ "
        "accuracy, and engineered a fallback recommendation engine ensuring 100% uptime."
    )
    pdf.ln(2)

    # --- Product Strategy ---
    pdf.section_heading("Product Strategy & Leadership")

    pdf.subsection_heading(
        "NextLeap PM Fellowship - Top Fellow",
        "",
        "Dec 2025 - Apr 2026"
    )
    pdf.bullet_point(
        "Ranked Top Fellow among 100+ fellows by designing MVP strategy, wireframes, KPI trees, "
        "and GTM prioritization."
    )
    pdf.ln(2)

    # --- Education ---
    pdf.section_heading("Education")
    pdf.subsection_heading(
        "Dayananda Sagar College of Engineering",
        "Bachelor of Engineering (B.E.), Chemical Engineering | Bengaluru, India",
        "2017 - 2021"
    )

    output_path = os.path.join(OUTPUT_DIR, "Neer_Agrawal_Technical_PM_Resume.pdf")
    pdf.output(output_path)
    print(f"[OK] Technical PM Resume saved: {output_path}")
    return output_path


# ============================================================================
# 3. UPDATED GENERAL RESUME
# ============================================================================
def generate_general_resume():
    pdf = ResumePDF()
    pdf.add_page()
    pdf.set_margins(14, 12, 14)
    pdf.header_section(NAME, CONTACT_LINE1, CONTACT_LINE2)

    # --- Professional Summary (refined) ---
    pdf.section_heading("Professional Summary")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.multi_cell(0, 5,
        "Product-minded Software Professional with 4.5+ years of experience bridging business strategy "
        "and technical execution. Proven track record of building 0-to-1 AI products (LLMs, RAG, GenAI) "
        "and shipping production systems across diverse domains. Recognized as Top Fellow at NextLeap PM "
        "Fellowship. Passionate about leveraging AI to solve real user problems at scale.",
        new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(2)

    # --- Skills ---
    pdf.section_heading("Skills")
    pdf.skills_section({
        "Product Management": "Product Strategy, Roadmap Planning, PRDs, User Stories, Acceptance Criteria, "
                              "RICE Prioritization, MVP Definition, Sprint Planning, GTM Strategy, "
                              "Customer Journey Mapping",
        "Vibe Coding & AI Tools": "RAG Systems, Cursor, Claude Code, Antigravity, LLM API Integration, "
                                  "Lovable, AI-assisted PRD Creation, Rapid Prototyping, Workflow Automation, "
                                  "AI Agents, Prompt Engineering",
        "Technical": "Java, Python, SQL, REST APIs, Microservices, MySQL, SQL Server, Google APIs, "
                     "FastAPI, Async Architecture",
        "Automation & QA": "Selenium, Robot Framework, Functional Testing, Regression Testing, UAT, "
                           "API Validation, Postman, SoapUI",
        "Tools": "Azure DevOps, Git, PyCharm, Claude, Cursor, Lovable, n8n"
    })

    # --- AI Product Development ---
    pdf.section_heading("AI Product Development")

    pdf.subsection_heading(
        "PM Opportunity Intelligence Platform",
        "Python, Async Architecture, Playwright, AI Automation, Telegram APIs, SQLite"
    )
    pdf.bullet_point(
        "Developed a production-grade PM opportunity intelligence platform using async orchestration, "
        "Playwright automation, and authenticated scraping workflows to aggregate and rank PM jobs "
        "across platforms like Naukri, Instahyre, Cutshort, and Lever."
    )
    pdf.bullet_point(
        "Eliminated 10+ hours/week of manual job hunting by engineering an AI-powered ATS and resume "
        "intelligence engine with automated job deduplication, resume targeting, and real-time Telegram delivery."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "Gifthesis - AI Gifting Assistant",
        "Groq LLM, Prompt Engineering, AI Workflows"
    )
    pdf.bullet_point(
        "Conducted user research to identify pain points in online gifting, translating insights into a "
        "3-step AI journey that improved user decision-making confidence and led to live deployment."
    )
    pdf.bullet_point(
        "Achieved more than 95% recommendation confidence accuracy using Groq LLM and structured prompt "
        "engineering, while ensuring 100% uptime through a fallback recommendation engine."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "Zomato - AI Restaurant Recommendation Engine",
        "FastAPI, Streamlit, LLM Personalization"
    )
    pdf.bullet_point(
        "Engineered a full-stack restaurant recommendation engine processing more than 1,000 restaurant "
        "data points using LLM-based user preference modeling."
    )
    pdf.bullet_point(
        "Architected and deployed a complete 6-phase product pipeline from data ingestion to production "
        "launch, delivering personalized restaurant recommendations in <3 seconds and reducing "
        "build-to-launch time to under 2 weeks."
    )
    pdf.ln(1)

    pdf.subsection_heading(
        "NextLeap PM Fellowship Chatbot",
        "RAG, FAISS, Groq LLM, Streamlit"
    )
    pdf.bullet_point(
        "Developed and deployed a RAG-based AI chatbot indexing 13 weeks of curriculum, 18 tools, and "
        "8 instructor profiles to enable instant contextual support for PM learners."
    )
    pdf.bullet_point(
        "Implemented FAISS semantic retrieval + Groq LLM, achieving <2 second response time with "
        "contextual accuracy, conversation history, and persistent session memory via Streamlit deployment."
    )
    pdf.ln(2)

    # --- Product Strategy ---
    pdf.section_heading("Product Strategy & Design")

    pdf.subsection_heading(
        "NextLeap PM Fellowship - Top Fellow",
        "",
        "Dec 2025 - Apr 2026"
    )
    pdf.bullet_point(
        "Top Fellow among 100+ fellows by designing MVP strategy, wireframes, KPI trees, and GTM prioritization."
    )
    pdf.ln(2)

    # --- Work Experience ---
    pdf.section_heading("Work Experience")

    pdf.subsection_heading(
        "Software Quality Engineer - Infosys",
        "Full-time | Bengaluru, India",
        "Nov 2021 - May 2026"
    )
    pdf.bullet_point(
        "Led release strategy and execution across large-scale API & microservices ecosystems for Retail "
        "and Energy domain clients, coordinating with more than 3 cross-functional engineering teams to "
        "ensure on-time feature delivery aligned with business goals."
    )
    pdf.bullet_point(
        "Spearheaded the product lifecycle of an internal Python-based automation framework from ideation "
        "to deployment, driving adoption across QA teams and reducing defect leakage by 20%."
    )
    pdf.bullet_point(
        "Optimized CI/CD workflows and automated validation pipelines, reducing retesting effort by 15% "
        "and accelerating deployment readiness for enterprise applications."
    )
    pdf.bullet_point(
        "Partnered with Product Owners, developers, and business stakeholders to translate ambiguous user "
        "requirements into actionable PRDs, user stories, and acceptance criteria for globally distributed "
        "Agile teams."
    )
    pdf.bullet_point(
        "Took ownership of delivery execution in highly ambiguous environments with limited roadmap clarity, "
        "proactively realigning priorities and ensuring 100% on-time release execution."
    )
    pdf.ln(2)

    # --- Education ---
    pdf.section_heading("Education")
    pdf.subsection_heading(
        "Dayananda Sagar College of Engineering",
        "Bachelor of Engineering (B.E.), Chemical Engineering | Bengaluru, India",
        "2017 - 2021"
    )

    output_path = os.path.join(OUTPUT_DIR, "Neer_Agrawal_Resume.pdf")
    pdf.output(output_path)
    print(f"[OK] General Resume saved (updated): {output_path}")
    return output_path


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("GENERATING TARGETED PM RESUME VARIANTS")
    print("=" * 60)
    print()
    
    generate_ai_pm_resume()
    generate_technical_pm_resume()
    generate_general_resume()
    
    print()
    print("=" * 60)
    print("ALL RESUMES GENERATED SUCCESSFULLY!")
    print("=" * 60)
