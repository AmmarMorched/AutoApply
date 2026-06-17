import json
from tracemalloc import start
import httpx
from app.config import settings


class ResumeStructurer:
    """Use AI to convert raw resume text into structured master resume format."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def structure(self, raw_text: str) -> dict:
        """Convert raw resume text into structured JSON."""
        
        text = raw_text[:8000]
        
        prompt = f"""You are an expert resume parser. Extract EVERY piece of information from this resume text.
BE EXHAUSTIVE. Do not skip anything. If a section exists in the text, include it.

=== RAW RESUME TEXT ===
{text}

=== INSTRUCTIONS ===
Extract ALL information. Nothing should be left out.

1. **Personal Info**: name, email, phone, location, linkedin, github — extract exactly as written
2. **Summary**: If the resume has a summary/profile section, use it. If not, write a 3-4 sentence summary based on their experience
3. **Experience**: For EACH job, extract:
   - title, company, dates (keep original format)
   - ALL bullet points (keep as many as exist, minimum 3, maximum 8 per role)
   - Keep original wording where possible
4. **Skills**: Extract EVERY skill mentioned — languages, frameworks, databases, tools, cloud, soft skills, methodologies. Be thorough.
5. **Projects**: If there's a projects section, extract EACH project with:
   - name, description, technologies used, link (if any), date
6. **Education**: ALL degrees/certifications — degree, school, year, GPA if mentioned
7. **Languages**: ALL languages with proficiency level
8. **Certifications**: ALL certifications — name, issuer, date, expiry if mentioned
9. **Other Sections**: If the resume has additional sections (awards, publications, volunteering, interests), include them in an "other" array

=== OUTPUT FORMAT ===
Return ONLY valid JSON (no markdown, no text outside JSON):
{{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "github": "",
  "summary": "",
  "experience": [
    {{
      "title": "",
      "company": "",
      "dates": "",
      "bullets": ["", ""]
    }}
  ],
  "skills": ["", ""],
  "projects": [
    {{
      "name": "",
      "description": "",
      "technologies": ["", ""],
      "link": "",
      "date": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "school": "",
      "year": ""
    }}
  ],
  "languages": ["Language (Proficiency)"],
  "certifications": ["Certification Name - Issuer (Year)"],
  "other": ["Any other notable information"]
}}

If a section doesn't exist in the resume, use an empty array []. DO NOT skip fields. Include ALL sections even if empty."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4000,
        }
        
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        content = data["choices"][0]["message"]["content"].strip()
        
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3]
        content = content.strip()
        
        result = self._extract_json(content)
        
        # Ensure ALL fields exist
        all_fields = [
            "name", "email", "phone", "location", "linkedin", "github",
            "summary", "experience", "skills", "projects", "education",
            "languages", "certifications", "other"
        ]
        for field in all_fields:
            if field not in result:
                if field in ["experience", "skills", "projects", "education", "languages", "certifications", "other"]:
                    result[field] = []
                else:
                    result[field] = ""
        
        return result
    

    def _extract_json(self, content: str) -> dict:
        """Robust JSON extraction from AI response."""
        if not content or not content.strip():
            return {}
    
        content = content.strip()
    
    # Try direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
    
    # Remove markdown code blocks
        if content.startswith("```"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
    
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
    
    # Find JSON between curly braces
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass
    
        return {}

    
    def validate_and_clean(self, structured_resume: dict) -> dict:
        """Clean and validate the structured resume."""
        
        action_verbs = [
            "Developed", "Built", "Led", "Managed", "Created", "Designed",
            "Implemented", "Optimized", "Reduced", "Increased", "Launched",
            "Automated", "Engineered", "Architected", "Coordinated",
            "Directed", "Established", "Generated", "Improved", "Integrated",
            "Migrated", "Orchestrated", "Redesigned", "Solved", "Streamlined",
            "Transformed", "Développé", "Créé", "Dirigé", "Géré", "Optimisé",
            "Conçu", "Implémenté", "Lancé", "Amélioré", "Automatisé"
        ]
        
        # Clean experience bullets
        if "experience" in structured_resume:
            for exp in structured_resume["experience"]:
                if "bullets" in exp:
                    cleaned = []
                    for bullet in exp["bullets"]:
                        bullet = bullet.strip().lstrip("*-•▶▸▪◦ ")
                        if bullet and len(bullet) > 5:
                            starts_strong = any(
                                bullet.lower().startswith(v.lower())
                                for v in action_verbs
                            )
                            if not starts_strong:
                                bullet = f"Developed {bullet[0].lower() + bullet[1:] if len(bullet) > 1 else bullet}"
                            cleaned.append(bullet)
                    exp["bullets"] = cleaned[:8]
        
        # Clean project descriptions
        if "projects" in structured_resume:
            for proj in structured_resume["projects"]:
                if "description" in proj and proj["description"]:
                    proj["description"] = proj["description"].strip()
                if "technologies" in proj and isinstance(proj["technologies"], str):
                    proj["technologies"] = [t.strip() for t in proj["technologies"].split(",")]
        
        # Deduplicate skills
        if "skills" in structured_resume:
            seen = set()
            unique = []
            for skill in structured_resume["skills"]:
                s = skill.strip()
                if s and s.lower() not in seen:
                    seen.add(s.lower())
                    unique.append(s)
            structured_resume["skills"] = unique
        
        return structured_resume