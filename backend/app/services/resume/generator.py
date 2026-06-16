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
        
        # Build contact line
        contact_parts = []
        if email: contact_parts.append(email)
        if phone: contact_parts.append(phone)
        if location: contact_parts.append(location)
        contact_line = " | ".join(contact_parts)
        
        # Build links line
        link_parts = []
        if linkedin: link_parts.append(linkedin)
        if github: link_parts.append(github)
        links_line = " | ".join(link_parts)
        
        # Build skills text
        skills_text = ", ".join(skills)
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 0.55in 0.6in 0.5in 0.6in;
  }}
  
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}
  
  body {{
    font-family: 'Calibri', 'Arial', sans-serif;
    font-size: 10.5pt;
    line-height: 1.25;
    color: #1a1a1a;
  }}
  
  .header {{
    text-align: center;
    margin-bottom: 6pt;
  }}
  
  .name {{
    font-size: 16pt;
    font-weight: 700;
    letter-spacing: 1pt;
    text-transform: uppercase;
    margin-bottom: 2pt;
  }}
  
  .contact {{
    font-size: 8.5pt;
    color: #555;
  }}
  
  .links {{
    font-size: 8.5pt;
    color: #555;
  }}
  
  .divider {{
    border: none;
    border-top: 1.5px solid #333;
    margin: 6pt 0;
  }}
  
  .section-title {{
    font-size: 11pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-top: 10pt;
    margin-bottom: 3pt;
    border-bottom: 0.5pt solid #999;
    padding-bottom: 1pt;
  }}
  
  .summary-text {{
    margin-bottom: 2pt;
  }}
  
  .skills-text {{
    margin-bottom: 2pt;
  }}
  
  .job-block {{
    margin-bottom: 6pt;
  }}
  
  .job-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }}
  
  .job-title {{
    font-weight: 700;
    font-size: 10.5pt;
  }}
  
  .job-dates {{
    font-size: 9pt;
    color: #666;
    white-space: nowrap;
  }}
  
  .job-company {{
    font-size: 9.5pt;
    color: #555;
    margin-bottom: 2pt;
  }}
  
  .bullets {{
    padding-left: 14pt;
    margin: 0;
  }}
  
  .bullets li {{
    font-size: 9.5pt;
    margin-bottom: 1pt;
    line-height: 1.2;
  }}
  
  .project-block {{
    margin-bottom: 4pt;
  }}
  
  .project-name {{
    font-weight: 700;
    font-size: 10pt;
  }}
  
  .project-tech {{
    font-size: 8.5pt;
    color: #666;
  }}
  
  .project-desc {{
    font-size: 9.5pt;
    margin-bottom: 2pt;
  }}
  
  .edu-line {{
    font-size: 10pt;
    margin-bottom: 1pt;
  }}
  
  .cert-list {{
    padding-left: 14pt;
    margin: 0;
  }}
  
  .cert-list li {{
    font-size: 9.5pt;
  }}
  
  .lang-text {{
    font-size: 10pt;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="name">{name}</div>
  <div class="contact">{contact_line}</div>
  {f'<div class="links">{links_line}</div>' if links_line else ''}
</div>

<hr class="divider">

{f'<div class="section-title">Professional Summary</div><div class="summary-text">{summary}</div>' if summary else ''}

{f'<div class="section-title">Technical Skills</div><div class="skills-text">{skills_text}</div>' if skills else ''}

{f'<div class="section-title">Professional Experience</div>' if experience else ''}
{self._build_experience_html(experience)}

{f'<div class="section-title">Projects</div>' if projects else ''}
{self._build_projects_html(projects)}

{f'<div class="section-title">Education</div>' if education else ''}
{self._build_education_html(education)}

{f'<div class="section-title">Certifications</div><ul class="cert-list">{self._build_certifications_html(certifications)}</ul>' if certifications else ''}

{f'<div class="section-title">Languages</div><div class="lang-text">{", ".join(languages)}</div>' if languages else ''}

</body>
</html>"""
        
        # Save HTML for debugging
        file_id = str(uuid.uuid4())
        html_path = os.path.join(self.storage_path, f"{file_id}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        # Generate PDF
        pdf_path = os.path.join(self.storage_path, f"{file_id}.pdf")
        
        from weasyprint import HTML
        HTML(string=html).write_pdf(pdf_path)
        
        # Clean up HTML
        os.remove(html_path)
        
        print(f"✅ PDF saved: {pdf_path}")
        return pdf_path
    
    def _build_experience_html(self, experience):
        html = ""
        for exp in experience:
            title = exp.get("title", "")
            company = exp.get("company", "")
            dates = exp.get("dates", "")
            bullets = exp.get("bullets", [])
            
            html += f"""
<div class="job-block">
  <div class="job-header">
    <span class="job-title">{title}</span>
    <span class="job-dates">{dates}</span>
  </div>
  <div class="job-company">{company}</div>
  <ul class="bullets">
    {''.join(f'<li>{b}</li>' for b in bullets)}
  </ul>
</div>"""
        return html
    
    def _build_projects_html(self, projects):
        html = ""
        for proj in projects:
            name = proj.get("name", "")
            tech = proj.get("technologies", [])
            tech_text = ", ".join(tech) if isinstance(tech, list) else str(tech)
            desc = proj.get("description", "")
            link = proj.get("link", "")
            date = proj.get("date", "")
            
            header = name
            if date:
                header += f" ({date})"
            
            html += f"""
<div class="project-block">
  <div class="project-name">{header}</div>
  {f'<div class="project-tech">Technologies: {tech_text}</div>' if tech_text else ''}
  {f'<div class="project-desc">{desc}</div>' if desc else ''}
</div>"""
        return html
    
    def _build_education_html(self, education):
        html = ""
        for edu in education:
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            year = edu.get("year", "")
            html += f'<div class="edu-line">{degree} — {school} ({year})</div>'
        return html
    
    def _build_certifications_html(self, certifications):
        return "".join(f"<li>{c}</li>" for c in certifications)