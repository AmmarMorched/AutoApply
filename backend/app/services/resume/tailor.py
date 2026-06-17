import json
from typing import List, Tuple, Dict
import httpx
from app.config import settings
from app.services.resume.ats_predictor import ATSPredictor


class ResumeTailor:
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.predictor = ATSPredictor()
    
    # ─────────────────────────────────────────────────
    # ANALYZE: Real ML + AI for natural language only
    # ─────────────────────────────────────────────────
    async def analyze(
        self,
        master_resume: dict,
        job_description: str,
        job_title: str,
        company: str
    ) -> dict:
        """Real ML-based analysis. AI only handles partial matches and summary text."""
        
        # Real prediction (math, not AI guessing)
        prediction = self.predictor.predict(master_resume, job_description)
        
        # AI only for natural language tasks
        analysis_summary = ""
        partial_matches = []
        try:
            ai_result = await self._ai_analyze_text(master_resume, job_description)
            if ai_result:
                partial_matches = ai_result.get("partial_matches", [])
                analysis_summary = ai_result.get("analysis_summary", "")
        except Exception as e:
            print(f"[ANALYZE] AI text analysis failed: {e}")
        
        return {
            **prediction,
            "partial_matches": partial_matches,
            "analysis_summary": analysis_summary or self._generate_summary(prediction),
            "candidate_skills_found": sorted(list(self.predictor._extract_skills_deep(
                self.predictor._extract_all_resume_text(master_resume)
            ).keys())),
            "job_skills_required": sorted(list(self.predictor._extract_skills_deep(
                job_description
            ).keys())),
        }
    
    def _generate_summary(self, prediction: dict) -> str:
        """Generate a human-readable summary from the prediction."""
        b = prediction.get("breakdown", {})
        s = prediction.get("skills_analysis", {})
        
        return (
            f"Overall match: {prediction.get('before_score', 0)}%. "
            f"Keyword match: {b.get('keyword_match', 0)}%, "
            f"Content similarity: {b.get('content_similarity', 0)}%, "
            f"Semantic match: {b.get('semantic_match', 0)}%. "
            f"Matching {s.get('matching_count', 0)} of {s.get('total_job_skills', 0)} required skills. "
            f"Missing {s.get('missing_count', 0)} skills. "
            f"After tailoring, estimated score: {prediction.get('predicted_after_score', 0)}%."
        )
    
    async def _ai_analyze_text(self, master_resume: dict, job_description: str) -> dict:
        """AI only handles natural language analysis (partial matches, summary)."""
        
        prompt = f"""Compare the candidate's resume with the job description.
Focus only on PARTIAL MATCHES — skills that are similar but not exact.

Examples:
- Candidate has "React" but job requires "React.js" → partial match
- Candidate has "REST APIs" but job requires "RESTful APIs" → partial match
- Candidate has "CI/CD pipelines" but job requires "CI/CD" → NOT a partial match (same thing)

=== JOB DESCRIPTION ===
{job_description[:2000]}

=== CANDIDATE RESUME ===
{json.dumps(master_resume, indent=2, ensure_ascii=False)[:3000]}

Return ONLY JSON:
{{
  "partial_matches": [{{"candidate_has": "React", "job_wants": "React.js"}}],
  "analysis_summary": "Brief 2-sentence analysis of candidate's fit"
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 500,
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            if response.status_code != 200:
                return None
            data = response.json()
        
        return self._extract_json(data["choices"][0]["message"]["content"])
    
    # ─────────────────────────────────────────────────
    # TAILOR: Rewrite resume using analysis
    # ─────────────────────────────────────────────────
    async def tailor(
        self,
        master_resume: dict,
        job_description: str,
        job_title: str,
        company: str,
        analysis: dict = None
    ) -> Tuple[dict, float, List[str], str]:
        """Tailor the resume using the analysis to maximize ATS match."""
        
        matching = analysis.get("matching_skills", []) if analysis else []
        missing = analysis.get("missing_skills", []) if analysis else []
        partial = analysis.get("partial_matches", []) if analysis else []
        
        matching_str = ", ".join(matching[:20]) if matching else "unknown"
        missing_str = ", ".join(missing[:10]) if missing else "none"
        partial_str = json.dumps(partial[:10]) if partial else "none"
        
        prompt = f"""You are an expert ATS resume optimizer. Rewrite this resume to maximize keyword matching.

=== TARGET JOB ===
{job_title} at {company}

=== JOB DESCRIPTION ===
{job_description[:3000]}

=== PRE-ANALYSIS ===
Skills the candidate HAS that match: {matching_str}
Skills the candidate is MISSING: {missing_str}
Partial matches to fix: {partial_str}

=== CANDIDATE RESUME ===
{json.dumps(master_resume, indent=2, ensure_ascii=False)}

=== RULES ===
1. Create a professional title that matches this job
2. Rewrite summary: use EXACT phrases from the JD for matching skills. For partial matches, use the JD's EXACT wording (e.g., if candidate has "React" and JD says "React.js", write "React.js")
3. Rewrite every experience bullet:
   - Inject matching keywords into bullets
   - Convert partial matches to JD's exact terminology
   - DO NOT add missing skills the candidate doesn't have
   - Use varied action verbs
4. Reorder skills: JD matches first (using JD's exact spelling), then rest
5. Keep projects, education, certifications, languages unchanged

Return ONLY JSON:
{{
  "title": "Tailored Professional Title",
  "summary": "COMPLETELY REWRITTEN summary with JD keywords...",
  "experience": [
    {{
      "title": "Original Title",
      "company": "Original Company",
      "dates": "Original Dates",
      "bullets": ["rewritten bullet with keyword", "rewritten bullet"]
    }}
  ],
  "skills": ["JD exact skill", "JD exact skill", "other skills..."],
  "keywords_matched": ["keyword1", "keyword2"],
  "match_score": 85,
  "changes_summary": "Brief description of what was changed and why"
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 3000,
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code}")
            data = response.json()
        
        content = data["choices"][0]["message"]["content"]
        result = self._extract_json(content)
        
        if not result:
            raise Exception("Failed to parse AI response")
        
        tailored = {
            "title": result.get("title", job_title),
            "summary": result.get("summary", master_resume.get("summary", "")),
            "experience": result.get("experience", master_resume.get("experience", [])),
            "skills": result.get("skills", master_resume.get("skills", [])),
            "projects": result.get("projects", master_resume.get("projects", [])),
        }
        
        match_score = result.get("match_score", 50)
        keywords = result.get("keywords_matched", [])
        changes = result.get("changes_summary", "")
        
        return tailored, match_score, keywords, changes
    
    # ─────────────────────────────────────────────────
    # JSON EXTRACTION (robust parsing)
    # ─────────────────────────────────────────────────
    def _extract_json(self, content: str) -> dict:
        """Robust JSON extraction from AI response."""
        if not content or not content.strip():
            return None
        
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
        
        # Try again after cleaning
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
        
        return None