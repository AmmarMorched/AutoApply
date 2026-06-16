import json
from typing import List, Tuple
import httpx
from app.config import settings


class ResumeTailor:
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def tailor(
        self,
        master_resume: dict,
        job_description: str,
        job_title: str,
        company: str
    ) -> Tuple[dict, float, List[str]]:
        
        prompt = f"""You are an expert ATS resume optimizer. Tailor this resume for a specific job.

=== JOB DETAILS ===
Title: {job_title}
Company: {company}

=== JOB DESCRIPTION ===
{job_description[:3000]}

=== CANDIDATE MASTER RESUME ===
{json.dumps(master_resume, indent=2, ensure_ascii=False)}

=== INSTRUCTIONS ===
1. Extract the 15 most important keywords/skills from the job description
2. Rewrite "summary" to 3-4 sentences incorporating the top 5-7 keywords naturally
3. For EACH job in "experience":
   - Keep the original title, company, and dates exactly
   - Rewrite ALL bullets to emphasize accomplishments relevant to THIS job
   - Use strong action verbs (Built, Led, Optimized, Designed, Implemented)
   - Include quantifiable results where available
   - DO NOT fabricate experience, technologies, or numbers
4. Reorder "skills": put matching skills first, keep all original skills, DO NOT add new ones
5. Keep "projects" exactly as-is (do not modify project names, descriptions, or technologies)
6. Calculate an honest match_score (0-100)

=== OUTPUT ===
Return ONLY valid JSON (no markdown, no explanation):
{{
  "summary": "rewritten professional summary...",
  "experience": [
    {{
      "title": "Original Title",
      "company": "Original Company",
      "dates": "Original Dates",
      "bullets": ["tailored bullet 1", "tailored bullet 2"]
    }}
  ],
  "skills": ["most relevant first", "second", "remaining skills..."],
  "projects": [{{"name": "", "description": "", "technologies": [], "link": "", "date": ""}}],
  "keywords_matched": ["keyword1", "keyword2"],
  "match_score": 85
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 3000,
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        content = data["choices"][0]["message"]["content"].strip()
        
        # Clean markdown if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:])
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        
        # Build tailored resume — merge tailored + original for untouched sections
        tailored = {
            "summary": result["summary"],
            "experience": result["experience"],
            "skills": result["skills"],
            "projects": result.get("projects", master_resume.get("projects", [])),
        }
        
        return tailored, result["match_score"], result["keywords_matched"]