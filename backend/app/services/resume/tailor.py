import json
from typing import List, Tuple
from openai import AsyncOpenAI
from app.config import settings

class ResumeTailor:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def tailor(
        self,
        master_resume: dict,
        job_description: str,
        job_title: str,
        company: str
    ) -> Tuple[dict, float, List[str]]:
        
        prompt = f"""You are an expert ATS resume optimizer.

JOB TITLE: {job_title}
COMPANY: {company}

JOB DESCRIPTION:
---
{job_description}
---

MASTER RESUME (JSON):
---
{json.dumps(master_resume, indent=2)}
---

INSTRUCTIONS:
1. Extract the top 12-15 keywords and required skills from the job description
2. Rewrite "summary" to naturally incorporate 5-7 of the most important keywords
3. For each position in "experience", rewrite bullets to emphasize relevant accomplishments. DO NOT fabricate experience or technologies.
4. Reorder "skills" so most relevant appear first
5. Do NOT add skills I don't have

Return ONLY valid JSON:
{{
  "summary": "rewritten summary",
  "experience": [
    {{
      "title": "original title",
      "company": "original company",
      "dates": "original dates",
      "bullets": ["tailored bullet 1", "tailored bullet 2"]
    }}
  ],
  "skills": ["most relevant first"],
  "keywords_matched": ["keyword1", "keyword2"],
  "match_score": 85
}}
"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        tailored = {
            "summary": result["summary"],
            "experience": result["experience"],
            "skills": result["skills"],
        }
        
        return tailored, result["match_score"], result["keywords_matched"]