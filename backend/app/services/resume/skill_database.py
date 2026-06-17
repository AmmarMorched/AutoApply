"""
Dynamic skill database. Grows automatically.
Sources: built-in base + user's resume + job descriptions seen.
"""
import re
import json
import os
from typing import Dict, List, Set
from pathlib import Path


class SkillDatabase:
    def __init__(self):
        self.data_dir = Path(__file__).parent / "skill_data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Core skill variants (maintained manually)
        self.skill_variants = self._load_base_variants()
        
        # Learned variants (grows automatically)
        self.learned_variants = self._load_learned()
        
        # Canonical lookup cache
        self._rebuild_canonical()
    
    def _load_base_variants(self) -> Dict[str, List[str]]:
        """Base skill variants. This is the seed — it grows from here."""
        return {
            # ── Programming Languages ────────────
            "python": ["python3", "python 3", "cpython"],
            "javascript": ["js", "vanilla js", "es6", "es2015", "ecmascript"],
            "typescript": ["ts", "type script"],
            "java": ["java se", "java ee", "jakarta ee", "j2ee"],
            "c#": ["csharp", "c sharp", ".net c#"],
            "c++": ["cpp", "c plus plus"],
            "go": ["golang", "go lang"],
            "rust": ["rust lang"],
            "ruby": ["ruby lang", "ruby on rails"],
            "php": ["php7", "php8", "php 7", "php 8"],
            "swift": ["swift lang", "ios swift"],
            "kotlin": ["kotlin lang", "android kotlin"],
            "scala": ["scala lang"],
            "r": ["r lang", "r programming"],
            "sql": ["tsql", "t-sql", "pl/sql", "plsql", "transact-sql"],
            "bash": ["shell", "shell script", "bash script", "sh"],
            
            # ── Frontend ─────────────────────────
            "react.js": ["react", "reactjs", "react js", "react.js", "react framework"],
            "angular": ["angularjs", "angular.js", "angular 2+", "angular2"],
            "vue.js": ["vue", "vuejs", "vue js", "vue3", "vue 3"],
            "next.js": ["next", "nextjs", "next js"],
            "nuxt.js": ["nuxt", "nuxtjs", "nuxt js"],
            "svelte": ["sveltejs", "svelte js"],
            "jquery": ["j query"],
            "html": ["html5", "html 5"],
            "css": ["css3", "css 3", "scss", "sass", "less"],
            "tailwind": ["tailwindcss", "tailwind css"],
            "bootstrap": ["bootstrap5", "bootstrap 5", "twitter bootstrap"],
            "redux": ["redux toolkit", "rtk", "reduxjs"],
            
            # ── Backend ──────────────────────────
            "node.js": ["node", "nodejs", "node js", "node runtime"],
            "express.js": ["express", "expressjs", "express js"],
            "django": ["django framework", "django rest", "drf"],
            "flask": ["flask framework", "flask python"],
            "fastapi": ["fast api", "fastapi python"],
            "spring": ["spring boot", "spring framework", "spring mvc", "springboot"],
            "laravel": ["laravel php", "laravel framework"],
            ".net": ["dotnet", "dot net", ".net core", "asp.net", "asp net"],
            "ruby on rails": ["rails", "ror"],
            "graphql": ["graph ql", "graphql api"],
            "rest api": ["restful", "restful api", "rest api", "rest architecture"],
            
            # ── Databases ────────────────────────
            "postgresql": ["postgres", "postgre sql", "pgsql", "postgre"],
            "mysql": ["my sql", "mysql database", "mariadb"],
            "mongodb": ["mongo", "mongo db", "mongod"],
            "redis": ["redis cache", "redis db"],
            "elasticsearch": ["elastic search", "elk stack", "elastic"],
            "dynamodb": ["dynamo db", "amazon dynamodb"],
            "cassandra": ["apache cassandra"],
            "neo4j": ["neo4j graph", "neo 4j"],
            "oracle": ["oracle db", "oracle database", "oracle sql"],
            "sql server": ["mssql", "ms sql", "microsoft sql server"],
            "sqlite": ["sqlite3", "sqlite 3"],
            "firebase": ["firebase db", "google firebase", "firestore"],
            "supabase": ["supabase db"],
            
            # ── Cloud & DevOps ───────────────────
            "aws": ["amazon web services", "aws cloud", "amazon aws"],
            "azure": ["microsoft azure", "azure cloud", "ms azure"],
            "gcp": ["google cloud", "google cloud platform", "gcloud"],
            "docker": ["docker container", "dockerized", "docker compose", "docker-compose"],
            "kubernetes": ["k8s", "kube", "kubernetes cluster"],
            "terraform": ["terraform iac", "hashicorp terraform"],
            "jenkins": ["jenkins ci", "jenkins pipeline"],
            "github actions": ["github action", "gh actions"],
            "gitlab ci": ["gitlab ci/cd", "gitlab pipeline"],
            "circleci": ["circle ci"],
            "ansible": ["ansible automation", "ansible playbook"],
            "prometheus": ["prometheus monitoring"],
            "grafana": ["grafana dashboard"],
            "elk stack": ["elk", "elasticsearch logstash kibana"],
            
            # ── Tools ────────────────────────────
            "git": ["git version control", "git vcs"],
            "github": ["github.com", "gh"],
            "gitlab": ["gitlab.com", "gl"],
            "bitbucket": ["bitbucket.org", "bb"],
            "jira": ["jira software", "atlassian jira"],
            "confluence": ["atlassian confluence"],
            "slack": ["slack workspace"],
            "linux": ["linux os", "unix", "ubuntu", "debian", "centos", "rhel", "fedora"],
            "nginx": ["nginx server", "nginx web server"],
            "apache": ["apache httpd", "apache server"],
            
            # ── Data & AI ────────────────────────
            "machine learning": ["ml", "machine-learning", "machinelearning"],
            "deep learning": ["dl", "deep-learning", "deeplearning"],
            "nlp": ["natural language processing", "natural language"],
            "computer vision": ["cv", "image recognition", "vision ai"],
            "tensorflow": ["tensor flow", "tf"],
            "pytorch": ["pytorch framework", "torch"],
            "keras": ["keras framework"],
            "scikit-learn": ["sklearn", "scikit learn"],
            "pandas": ["pandas python", "python pandas"],
            "numpy": ["numpy python", "np"],
            "spark": ["apache spark", "pyspark"],
            "hadoop": ["apache hadoop", "hdfs"],
            "kafka": ["apache kafka", "kafka streaming"],
            "rabbitmq": ["rabbit mq", "rabbit"],
            "airflow": ["apache airflow", "airflow dag"],
            
            # ── Methodologies ────────────────────
            "agile": ["agile methodology", "agile development"],
            "scrum": ["scrum methodology", "scrum master", "scrum agile"],
            "kanban": ["kanban board", "kanban methodology"],
            "tdd": ["test driven development", "test-driven"],
            "ci/cd": ["ci cd", "continuous integration", "continuous deployment", "continuous delivery"],
            "devops": ["dev ops", "development operations"],
            "microservices": ["micro services", "microservice architecture"],
            "serverless": ["server less", "serverless architecture"],
            "mvc": ["model view controller", "mvc pattern"],
            "oop": ["object oriented programming", "object-oriented"],
            
            # ── Soft Skills ──────────────────────
            "leadership": ["team leadership", "leading teams"],
            "mentoring": ["mentorship", "coaching", "mentored"],
            "communication": ["written communication", "verbal communication"],
            "problem solving": ["problem-solving", "troubleshooting"],
            "teamwork": ["team collaboration", "cross-functional team"],
            "project management": ["project management", "pm", "project planning"],
        }
    
    def _load_learned(self) -> Dict[str, List[str]]:
        """Load learned variants from disk."""
        path = self.data_dir / "learned_variants.json"
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}
    
    def _save_learned(self):
        """Save learned variants to disk."""
        path = self.data_dir / "learned_variants.json"
        with open(path, "w") as f:
            json.dump(self.learned_variants, f, indent=2)
    
    def _rebuild_canonical(self):
        """Rebuild the canonical lookup from all variants."""
        self.canonical = {}
        all_variants = {**self.skill_variants, **self.learned_variants}
        for canonical, variants in all_variants.items():
            self.canonical[canonical] = canonical
            for variant in variants:
                self.canonical[variant] = canonical
    
    def normalize(self, skill: str) -> str:
        """Convert any skill variant to its canonical form."""
        skill_lower = skill.lower().strip()
        return self.canonical.get(skill_lower, skill_lower)
    
    def learn_from_job(self, job_text: str):
        """Learn new skill variants from job descriptions.
        Looks for patterns like 'React.js (React)' or 'K8s/Kubernetes'."""
        
        # Pattern 1: "FullName (Abbreviation)" or "Abbreviation (FullName)"
        patterns = [
            r'(\w[\w\s\.\#\+]{1,30})\s*\((\w{1,10})\)',  # React.js (React)
            r'(\w{1,10})\s*\((\w[\w\s\.\#\+]{1,30})\)',  # AWS (Amazon Web Services)
            r'(\w[\w\s\.\#\+]{2,30})\s*/\s*(\w[\w\s\.\#\+]{2,30})',  # Kubernetes/K8s
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, job_text)
            for match in matches:
                a, b = match[0].strip().lower(), match[1].strip().lower()
                if a and b and len(a) > 1 and len(b) > 1:
                    # Add both directions
                    self._add_learned(a, [b])
                    self._add_learned(b, [a])
        
        self._save_learned()
        self._rebuild_canonical()
    
    def learn_from_resume(self, resume_data: dict):
        """Learn from user's resume — how they spell their skills."""
        skills_list = resume_data.get("skills", [])
        
        for skill in skills_list:
            skill_lower = skill.lower().strip()
            # If we don't know this skill at all, add it
            if skill_lower not in self.canonical:
                self._add_learned(skill_lower, [])
        
        self._save_learned()
        self._rebuild_canonical()
    
    def _add_learned(self, canonical: str, variants: List[str]):
        """Add a learned variant pair."""
        if canonical not in self.learned_variants:
            self.learned_variants[canonical] = []
        
        for v in variants:
            if v not in self.learned_variants[canonical] and v != canonical:
                self.learned_variants[canonical].append(v)
    
    def get_all_known_skills(self) -> Set[str]:
        """Get all canonical skill names."""
        return set(self.canonical.values())
    
    def find_in_text(self, text: str) -> Dict[str, int]:
        """Find all known skills in text. Returns {canonical: frequency}."""
        from collections import Counter
        text_lower = text.lower()
        found = Counter()
        
        # Check all known variants
        for variant, canonical in self.canonical.items():
            pattern = r'\b' + re.escape(variant) + r'\b'
            matches = re.findall(pattern, text_lower)
            if matches:
                found[canonical] += len(matches)
        
        # Also extract ALL CAPS acronyms
        acronyms = re.findall(r'\b[A-Z]{2,6}\b', text)
        stop_words = {"THE", "AND", "FOR", "YOU", "OUR", "ALL", "ARE", "BUT",
                      "NOT", "ITS", "CAN", "HAS", "HAD", "WAS", "WERE", "WILL",
                      "WITH", "FROM", "THEY", "THIS", "THAT", "HAVE", "BEEN"}
        for acr in acronyms:
            if acr not in stop_words:
                acr_lower = acr.lower()
                if acr_lower not in found:
                    found[acr_lower] += 1
        
        return dict(found)


# Global instance
skill_db = SkillDatabase()