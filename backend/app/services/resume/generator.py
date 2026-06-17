import uuid
import os
from app.config import settings


class PdfGenerator:
    def __init__(self):
        self.storage_path = getattr(settings, 'storage_path', './generated_resumes')
        os.makedirs(self.storage_path, exist_ok=True)
    
    def generate(self, resume_data: dict) -> str:
        """Generate a single-page ATS-optimized PDF resume."""
        
        name = resume_data.get("name", "")
        title = resume_data.get("title", "")
        email = resume_data.get("email", "")
        phone = resume_data.get("phone", "")
        location = resume_data.get("location", "")
        linkedin = resume_data.get("linkedin", "")
        github = resume_data.get("github", "")
        summary = resume_data.get("summary", "")
        skills = resume_data.get("skills", [])
        experience = resume_data.get("experience", [])
        projects = resume_data.get("projects", [])
        education = resume_data.get("education", [])
        certifications = resume_data.get("certifications", [])
        languages = resume_data.get("languages", [])
        
        # Contact line: email | phone | location
        contact_parts = [p for p in [email, phone, location] if p]
        contact_line = " | ".join(contact_parts)
        
        # Links line: linkedin | github
        link_parts = [p for p in [linkedin, github] if p]
        links_line = " | ".join(link_parts)
        
        # Skills text
        skills_text = ", ".join(skills)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 0.45in 0.5in 0.4in 0.5in;
  }}
  
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}
  
  body {{
    font-family: Calibri, Arial, Helvetica, sans-serif;
    font-size: 10pt;
    line-height: 1.22;
    color: #000000;
  }}
  
  .header {{
    text-align: center;
    margin-bottom: 6pt;
  }}
  
  .name {{
    font-size: 16pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5pt;
    margin-bottom: 4pt;
  }}
  
  .title-line {{
    font-size: 10.5pt;
    font-weight: 600;
    color: #222222;
    margin-bottom: 3pt;
  }}
  
  .contact-line {{
    font-size: 9pt;
    color: #444444;
  }}
  
  .links-line {{
    font-size: 9pt;
    color: #666666;
    margin-top: 1pt;
  }}
  
  .divider {{
    border: none;
    border-top: 1.5px solid #000000;
    margin: 7pt 0 8pt 0;
  }}
  
  .section-title {{
    font-size: 10.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-top: 9pt;
    margin-bottom: 3pt;
    border-bottom: 0.75px solid #666666;
    padding-bottom: 2pt;
  }}
  
  .summary-text {{
    margin-bottom: 3pt;
    text-align: justify;
  }}
  
  .skills-text {{
    margin-bottom: 3pt;
  }}
  
  .job-block {{
    margin-bottom: 5pt;
  }}
  
  .job-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }}
  
  .job-title {{
    font-weight: 700;
    font-size: 10pt;
  }}
  
  .job-dates {{
    font-size: 8.5pt;
    color: #444444;
    white-space: nowrap;
  }}
  
  .job-company {{
    font-size: 9pt;
    font-style: italic;
    color: #333333;
    margin-bottom: 2pt;
  }}
  
  ul {{
    padding-left: 15pt;
    margin-bottom: 3pt;
  }}
  
  li {{
    font-size: 9pt;
    margin-bottom: 0.5pt;
    line-height: 1.18;
  }}
  
  .project-block {{
    margin-bottom: 3pt;
  }}
  
  .project-name {{
    font-weight: 700;
    font-size: 9.5pt;
  }}
  
  .project-date {{
    font-size: 8pt;
    color: #666666;
  }}
  
  .project-tech {{
    font-size: 8.5pt;
    color: #444444;
    margin-bottom: 1pt;
  }}
  
  .project-desc {{
    font-size: 9pt;
    margin-bottom: 2pt;
  }}
  
  .edu-line {{
    font-size: 9pt;
    margin-bottom: 1pt;
  }}
  
  .cert-item {{
    font-size: 9pt;
    margin-bottom: 0.5pt;
  }}
  
  .lang-line {{
    font-size: 9pt;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="name">{name}</div>
  {f'<div class="title-line">{title}</div>' if title else ''}
  <div class="contact-line">{contact_line}</div>
  {f'<div class="links-line">{links_line}</div>' if links_line else ''}
</div>

<hr class="divider">

{f'<div class="section-title">Professional Summary</div><div class="summary-text">{summary}</div>' if summary else ''}

{f'<div class="section-title">Technical Skills</div><div class="skills-text">{skills_text}</div>' if skills else ''}

{f'<div class="section-title">Professional Experience</div>' if experience else ''}
{self._build_experience(experience)}

{f'<div class="section-title">Projects</div>' if projects else ''}
{self._build_projects(projects)}

{f'<div class="section-title">Education</div>' if education else ''}
{self._build_education(education)}

{f'<div class="section-title">Certifications</div>' if certifications else ''}
{self._build_certifications(certifications)}

{f'<div class="section-title">Languages</div><div class="lang-line">{", ".join(languages)}</div>' if languages else ''}

</body>
</html>"""
        
        # Save HTML temporarily
        file_id = str(uuid.uuid4())[:8]
        html_path = os.path.join(self.storage_path, f"{file_id}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        # Generate PDF
        pdf_path = os.path.join(self.storage_path, f"{file_id}.pdf")
        
        from weasyprint import HTML
        HTML(string=html).write_pdf(pdf_path)
        
        # Clean up HTML
        if os.path.exists(html_path):
            os.remove(html_path)
        
        print(f"✅ PDF saved: {pdf_path}")
        return pdf_path
    
    def _build_experience(self, experience: list) -> str:
        html = ""
        for exp in experience:
            job_title = exp.get("title", "")
            company = exp.get("company", "")
            dates = exp.get("dates", "")
            bullets = exp.get("bullets", [])
            
            html += f"""
<div class="job-block">
  <div class="job-header">
    <span class="job-title">{job_title}</span>
    <span class="job-dates">{dates}</span>
  </div>
  <div class="job-company">{company}</div>
  <ul>
    {''.join(f'<li>{b}</li>' for b in bullets)}
  </ul>
</div>"""
        return html
    
    def _build_projects(self, projects: list) -> str:
        html = ""
        for proj in projects:
            name = proj.get("name", "")
            date = proj.get("date", "")
            tech = proj.get("technologies", [])
            tech_text = ", ".join(tech) if isinstance(tech, list) else str(tech)
            desc = proj.get("description", "")
            link = proj.get("link", "")
            
            header = name
            if date:
                header += f' <span class="project-date">({date})</span>'
            
            html += f"""
<div class="project-block">
  <div class="project-name">{header}</div>
  {f'<div class="project-tech">Technologies: {tech_text}</div>' if tech_text else ''}
  {f'<div class="project-desc">{desc}</div>' if desc else ''}
  {f'<div class="project-tech">{link}</div>' if link else ''}
</div>"""
        return html
    
    def _build_education(self, education: list) -> str:
        html = ""
        for edu in education:
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            year = edu.get("year", "")
            parts = [degree, school, f"({year})" if year else ""]
            line = " — ".join(p for p in parts if p)
            html += f'<div class="edu-line">{line}</div>'
        return html
    
    def _build_certifications(self, certifications: list) -> str:
        if not certifications:
            return ""
        html = '<ul>'
        for cert in certifications:
            html += f'<li class="cert-item">{cert}</li>'
        html += '</ul>'
        return html