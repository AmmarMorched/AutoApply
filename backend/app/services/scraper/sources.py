"""
Job site definitions. Add new sites here.
Each site needs: name, url_template, type, and optional selectors.
"""

SITES = [
    # ── Direct scraping (HTML) ──────────────────────
    {
        "name": "TunisieTravail",
        "type": "html",
        "url": "https://www.tunisietravail.net/?s={keyword}",
        "enabled": True,
        "selectors": {
            "container": "article, .post, .listing, .entry",
            "title": "h2, h3, .entry-title, .post-title",
            "description": ".entry-content, .excerpt, p",
            "link": "a[href*='emploi'], a[href*='offre'], a[href*='recrut'], h2 a, .entry-title a",
        },
        "base_url": "https://www.tunisietravail.net",
    },
    
    # ── LinkedIn (public API) ──────────────────────
    {
        "name": "LinkedIn",
        "type": "linkedin_api",
        "url": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location=Tunisia&start=0",
        "enabled": True,
        "selectors": {
            "container": "div.base-card, li.jobs-search-results__list-item",
            "title": "h3, .base-search-card__title",
            "company": "h4, .base-search-card__subtitle",
            "link": "a[href*='/jobs/view/']",
        },
    },
    
    # ── RSS feeds ──────────────────────────────────
    {
        "name": "TanitJobs",
        "type": "rss",
        "url": "https://www.tanitjobs.com/feed/?post_type=job&s={keyword}",
        "enabled": False,  # Test first, enable if works
    },
    {
        "name": "Keejob",
        "type": "rss",
        "url": "https://www.keejob.com/feed/?s={keyword}",
        "enabled": False,
    },
    {
        "name": "EmploiTunisie",
        "type": "rss",
        "url": "https://www.emploitunisie.com/feed/?s={keyword}",
        "enabled": False,
    },
    {
        "name": "OptionCarriere",
        "type": "rss",
        "url": "https://www.optioncarriere.tn/feed/?s={keyword}",
        "enabled": False,
    },
    
    # ── Aggregators ────────────────────────────────
    {
        "name": "CareerJet",
        "type": "html",
        "url": "https://www.careerjet.tn/recherche/emplois?s={keyword}&l=Tunisie",
        "enabled": False,  # Test first
        "selectors": {
            "container": ".job, .result, article",
            "title": "h2, .title, a",
            "company": ".company, .employer",
            "link": "a[href*='/job/']",
        },
    },
    {
        "name": "Jooble",
        "type": "html",
        "url": "https://tn.jooble.org/emploi-{keyword}/Tunisie",
        "enabled": False,
        "selectors": {
            "container": "article, .vacancy, .job",
            "title": "h2, .title, a",
            "company": ".company, .employer-name",
            "link": "a[href]",
        },
    },
    
    # ── Remote job boards ──────────────────────────
    {
        "name": "RemoteOK",
        "type": "html",
        "url": "https://remoteok.com/remote-{keyword}-jobs",
        "enabled": False,
        "selectors": {
            "container": "tr.job, .job",
            "title": "h2, .company-position",
            "company": "h3, .company-name",
            "link": "a[href*='remoteok']",
        },
    },
    
    # Add more sites here...
    # {
    #     "name": "Site Name",
    #     "type": "html",  # or "rss" or "linkedin_api"
    #     "url": "https://example.com/search?q={keyword}",
    #     "enabled": True,
    #     "selectors": {
    #         "container": ".job-listing",
    #         "title": ".job-title",
    #         "company": ".company-name",
    #         "link": "a.apply-link",
    #     },
    # },
]