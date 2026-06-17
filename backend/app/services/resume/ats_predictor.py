"""
ATS Score Predictor - Real ML-based prediction.
No AI guessing. Uses keyword matching + TF-IDF + semantic similarity.
"""
import re
import numpy as np
from typing import Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from app.services.resume.skill_database import skill_db


class ATSPredictor:
    """
    Predicts ATS compatibility scores based on:
    1. Keyword match rate (exact + fuzzy via skill database)
    2. TF-IDF similarity
    3. Semantic similarity (if sentence-transformers available)
    4. Section completeness
    5. Experience level match
    """
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        self.scaler = StandardScaler()
        self.skill_db = skill_db
        self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize sentence transformer for semantic similarity."""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_embeddings = True
            print("[ATS] Sentence transformer loaded")
        except Exception as e:
            print(f"[ATS] Sentence transformer not available: {e}")
            self.embedder = None
            self.use_embeddings = False
    
    def _extract_skills_deep(self, text: str) -> Dict[str, int]:
        """Deep skill extraction using the dynamic skill database."""
        return self.skill_db.find_in_text(text)
    
    def _extract_all_resume_text(self, resume: dict) -> str:
        """Combine all resume fields into one text for analysis."""
        parts = []
        
        parts.append(resume.get("summary", ""))
        parts.append(resume.get("title", ""))
        parts.append(" ".join(resume.get("skills", [])))
        
        for exp in resume.get("experience", []):
            parts.append(exp.get("title", ""))
            parts.append(exp.get("company", ""))
            parts.append(" ".join(exp.get("bullets", [])))
        
        for proj in resume.get("projects", []):
            parts.append(proj.get("name", ""))
            parts.append(proj.get("description", ""))
            parts.append(" ".join(proj.get("technologies", [])))
        
        for edu in resume.get("education", []):
            parts.append(f"{edu.get('degree', '')} {edu.get('school', '')}")
        
        parts.extend(resume.get("certifications", []))
        parts.extend(resume.get("languages", []))
        
        return " ".join(parts)
    
    def _calculate_keyword_score(self, resume_text: str, job_text: str) -> float:
        """Score based on keyword overlap with normalization."""
        resume_skills = self._extract_skills_deep(resume_text)
        job_skills = self._extract_skills_deep(job_text)
        
        if not job_skills:
            return 0.0
        
        match_score = 0
        total_weight = 0
        
        for skill, freq in job_skills.items():
            weight = min(freq, 3)
            total_weight += weight
            
            if skill in resume_skills:
                match_score += weight * min(1.0, resume_skills[skill] / freq)
        
        if total_weight == 0:
            return 0.0
        
        return match_score / total_weight
    
    def _calculate_tfidf_score(self, resume_text: str, job_text: str) -> float:
        """TF-IDF cosine similarity score."""
        try:
            tfidf_matrix = self.tfidf.fit_transform([job_text, resume_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(similarity[0][0])
        except:
            return 0.0
    
    def _calculate_semantic_score(self, resume_text: str, job_text: str) -> float:
        """Semantic similarity using sentence embeddings."""
        if not self.use_embeddings or not self.embedder:
            return 0.0
        
        try:
            job_embedding = self.embedder.encode(job_text[:2000])
            resume_embedding = self.embedder.encode(resume_text[:2000])
            similarity = cosine_similarity([job_embedding], [resume_embedding])
            return float(similarity[0][0])
        except:
            return 0.0
    
    def _calculate_section_score(self, resume: dict) -> float:
        """Score based on resume completeness."""
        sections = {
            "summary": 0.20,
            "skills": 0.20,
            "experience": 0.30,
            "education": 0.15,
            "projects": 0.10,
            "certifications": 0.05,
        }
        
        score = 0.0
        if resume.get("summary"):
            score += sections["summary"]
        if resume.get("skills") and len(resume.get("skills", [])) >= 5:
            score += sections["skills"]
        if resume.get("experience") and len(resume.get("experience", [])) > 0:
            score += sections["experience"]
        if resume.get("education"):
            score += sections["education"]
        if resume.get("projects") and len(resume.get("projects", [])) > 0:
            score += sections["projects"]
        if resume.get("certifications") and len(resume.get("certifications", [])) > 0:
            score += sections["certifications"]
        
        return score
    
    def _calculate_experience_match(self, resume: dict, job_text: str) -> float:
        """Check if experience level matches."""
        job_lower = job_text.lower()
        resume_exp_years = 0
        
        for exp in resume.get("experience", []):
            dates = exp.get("dates", "")
            years = re.findall(r'(\d{4})', dates)
            if len(years) >= 2:
                resume_exp_years += int(years[-1]) - int(years[0])
            elif len(years) == 1:
                resume_exp_years += 2
        
        job_year_patterns = [
            (r'(\d+)\+?\s*years?\s*(of\s*)?experience', 1),
            (r'(\d+)[\+-]\s*ans?\s*d[\'e]\s*exp', 1),
            (r'minimum\s*(\d+)\s*years?', 1),
        ]
        
        required_years = 0
        for pattern, group in job_year_patterns:
            match = re.search(pattern, job_lower)
            if match:
                required_years = int(match.group(group))
                break
        
        if required_years == 0:
            if any(kw in job_lower for kw in ["senior", "sénior", "lead", "expert"]):
                required_years = 5
            elif any(kw in job_lower for kw in ["junior", "débutant", "entry"]):
                required_years = 1
            else:
                required_years = 3
        
        if required_years == 0:
            return 1.0
        
        ratio = resume_exp_years / required_years
        return min(1.0, ratio)
    
    def predict(self, resume: dict, job_description: str) -> dict:
        """
        Predict ATS compatibility.
        Returns before_score, predicted_after_score, and detailed breakdown.
        """
        
        resume_text = self._extract_all_resume_text(resume)
        job_text = job_description
        
        # Individual scores
        keyword_score = self._calculate_keyword_score(resume_text, job_text)
        tfidf_score = self._calculate_tfidf_score(resume_text, job_text)
        semantic_score = self._calculate_semantic_score(resume_text, job_text)
        section_score = self._calculate_section_score(resume)
        experience_score = self._calculate_experience_match(resume, job_text)
        
        # Weights
        weights = {
            "keyword": 0.35,
            "tfidf": 0.25,
            "semantic": 0.15,
            "section": 0.10,
            "experience": 0.15,
        }
        
        # Before score
        before_score = (
            keyword_score * weights["keyword"] +
            tfidf_score * weights["tfidf"] +
            semantic_score * weights["semantic"] +
            section_score * weights["section"] +
            experience_score * weights["experience"]
        ) * 100
        
        # Predicted after score (with realistic improvements from tailoring)
        after_improvements = {
            "keyword_improvement": min(0.30, (1.0 - keyword_score) * 0.6),
            "tfidf_improvement": min(0.15, (1.0 - tfidf_score) * 0.4),
            "semantic_improvement": min(0.10, (1.0 - semantic_score) * 0.3),
        }
        
        predicted_after = (
            (keyword_score + after_improvements["keyword_improvement"]) * weights["keyword"] +
            (tfidf_score + after_improvements["tfidf_improvement"]) * weights["tfidf"] +
            (semantic_score + after_improvements["semantic_improvement"]) * weights["semantic"] +
            section_score * weights["section"] +
            experience_score * weights["experience"]
        ) * 100
        
        # Cap scores
        before_score = min(100, round(before_score))
        predicted_after = min(98, round(predicted_after))
        
        # Skills analysis
        resume_skills = set(self._extract_skills_deep(resume_text).keys())
        job_skills = set(self._extract_skills_deep(job_text).keys())
        matching = resume_skills & job_skills
        missing = job_skills - resume_skills
        
        return {
            "before_score": before_score,
            "predicted_after_score": predicted_after,
            "improvement": predicted_after - before_score,
            "breakdown": {
                "keyword_match": round(keyword_score * 100),
                "content_similarity": round(tfidf_score * 100),
                "semantic_match": round(semantic_score * 100),
                "resume_completeness": round(section_score * 100),
                "experience_fit": round(experience_score * 100),
            },
            "skills_analysis": {
                "matching_skills": sorted(list(matching)),
                "missing_skills": sorted(list(missing)),
                "matching_count": len(matching),
                "missing_count": len(missing),
                "total_job_skills": len(job_skills),
            },
            "confidence": "high" if len(job_skills) > 10 else "medium" if len(job_skills) > 5 else "low",
        }