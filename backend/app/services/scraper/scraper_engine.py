"""
Scraping engine. Reads site definitions from sources.py
and runs them. Add sites in sources.py, not here.
"""
from typing import List, Optional
import hashlib
import httpx
from bs4 import BeautifulSoup
from app.schemas.job import JobCreate
from app.services.scraper.sources import SITES


class ScraperEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
    
    async def _fetch(self, url: str) -> str:
        async with httpx.AsyncClient(verify=False, timeout=20, follow_redirects=True) as client:
            response = await client.get(url, headers=self.headers)
            return response.text
    
    def _detect_experience_level(self, title: str, description: str) -> Optional[str]:
        text = f"{title} {description}".lower()
        
        if any(kw in text for kw in ["lead", "chef de", "directeur", "director", "head of"]):
            return "lead"
        if any(kw in text for kw in ["senior", "sénior", "manager", "expert", "confirmé", "5+", "5 ans", "6 ans", "7 ans", "8 ans", "9 ans", "10 ans"]):
            return "senior"
        if any(kw in text for kw in ["junior", "débutant", "stagiaire", "intern", "graduate", "1 an", "2 ans", "pfe", "stage"]):
            return "junior"
        if any(kw in text for kw in ["3 ans", "4 ans", "3-5", "mid-level"]):
            return "mid"
        
        return None
    
    # ── HTML scraper ────────────────────────────────
    async def _scrape_html(self, site: dict, keyword: str) -> List[JobCreate]:
        jobs = []
        selectors = site.get("selectors", {})
        base_url = site.get("base_url", "")
        
        try:
            url = site["url"].format(keyword=keyword)
            print(f"  Fetching: {url}")
            html = await self._fetch(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            containers = soup.select(selectors.get("container", "article"))
            print(f"  Found {len(containers)} items")
            
            for item in containers:
                title_el = item.select_one(selectors.get("title", "h2, h3"))
                company_el = item.select_one(selectors.get("company", ".company"))
                desc_el = item.select_one(selectors.get("description", "p"))
                link_el = item.select_one(selectors.get("link", "a[href]"))
                
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                if len(title) < 5 or len(title) > 200:
                    continue
                
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                description = desc_el.get_text(strip=True)[:1000] if desc_el else ""
                
                apply_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    apply_url = href if href.startswith("http") else f"{base_url}{href}"
                
                exp_level = self._detect_experience_level(title, description)
                ext_id = hashlib.md5(f"{title}-{company}-{site['name']}".encode()).hexdigest()
                
                jobs.append(JobCreate(
                    external_id=ext_id,
                    title=title,
                    company=company,
                    location="Tunisia",
                    description=description,
                    apply_url=apply_url,
                    source=site["name"].lower(),
                    experience_level=exp_level,
                    keywords_found=[keyword],
                ))
            
        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {e}")
        
        return jobs
    
    # ── LinkedIn scraper ────────────────────────────
    async def _scrape_linkedin(self, site: dict, keyword: str) -> List[JobCreate]:
        jobs = []
        selectors = site.get("selectors", {})
        
        try:
            url = site["url"].format(keyword=keyword)
            print(f"  Fetching: {url}")
            html = await self._fetch(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            cards = soup.select(selectors.get("container", "div.base-card"))
            print(f"  Found {len(cards)} cards")
            
            for card in cards:
                title_el = card.select_one(selectors.get("title", "h3"))
                company_el = card.select_one(selectors.get("company", "h4"))
                link_el = card.select_one(selectors.get("link", "a[href]"))
                
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                
                apply_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    apply_url = href.split("?")[0] if "?" in href else href
                
                exp_level = self._detect_experience_level(title, "")
                ext_id = hashlib.md5(f"{title}-{company}-linkedin".encode()).hexdigest()
                
                jobs.append(JobCreate(
                    external_id=ext_id,
                    title=title,
                    company=company,
                    location="Tunisia",
                    apply_url=apply_url,
                    source="linkedin",
                    experience_level=exp_level,
                    keywords_found=[keyword],
                ))
        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {e}")
        
        return jobs
    
    # ── RSS scraper ─────────────────────────────────
    async def _scrape_rss(self, site: dict, keyword: str) -> List[JobCreate]:
        jobs = []
        
        try:
            url = site["url"].format(keyword=keyword)
            print(f"  Fetching: {url}")
            html = await self._fetch(url)
            soup = BeautifulSoup(html, 'xml')
            
            items = soup.select("item")
            print(f"  Found {len(items)} items")
            
            for item in items:
                title_el = item.select_one("title")
                desc_el = item.select_one("description")
                link_el = item.select_one("link")
                
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                description = desc_el.get_text(strip=True)[:1000] if desc_el else ""
                apply_url = link_el.get_text(strip=True) if link_el else ""
                
                exp_level = self._detect_experience_level(title, description)
                ext_id = hashlib.md5(f"{title}-{site['name']}".encode()).hexdigest()
                
                jobs.append(JobCreate(
                    external_id=ext_id,
                    title=title,
                    company="See description",
                    location="Tunisia",
                    description=description,
                    apply_url=apply_url,
                    source=site["name"].lower(),
                    experience_level=exp_level,
                    keywords_found=[keyword],
                ))
        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {e}")
        
        return jobs
    
    # ── Run single site ─────────────────────────────
    async def _scrape_site(self, site: dict, keywords: List[str]) -> List[JobCreate]:
        site_jobs = []
        
        for keyword in keywords:
            if site["type"] == "html":
                result = await self._scrape_html(site, keyword)
            elif site["type"] == "linkedin_api":
                result = await self._scrape_linkedin(site, keyword)
            elif site["type"] == "rss":
                result = await self._scrape_rss(site, keyword)
            else:
                print(f"  Unknown type: {site['type']}")
                result = []
            
            site_jobs.extend(result)
        
        return site_jobs
    
    # ── Run all enabled sites ───────────────────────
    async def search_all(self, keywords: List[str]) -> List[JobCreate]:
        all_jobs = []
        enabled_sites = [s for s in SITES if s.get("enabled", False)]
        
        print(f"\n{'='*50}")
        print(f"🔍 Scraping {len(enabled_sites)} sites for: {keywords}")
        print(f"{'='*50}")
        
        for site in enabled_sites:
            print(f"\n▶ [{site['name']}] ({site['type']})")
            jobs = await self._scrape_site(site, keywords)
            print(f"   → {len(jobs)} jobs")
            all_jobs.extend(jobs)
        
        print(f"\n{'='*50}")
        print(f"📊 TOTAL: {len(all_jobs)} jobs")
        print(f"{'='*50}\n")
        
        return all_jobs