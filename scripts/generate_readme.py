import os
import re
import sys

# Mappings of technology name to Devicon SVGs
DEVICON_MAP = {
    "python": "python/python-original.svg",
    "django": "https://cdn.simpleicons.org/django/white",
    "django rest framework": "https://cdn.simpleicons.org/django/white",
    "django rest framework (drf)": "https://cdn.simpleicons.org/django/white",
    "drf": "https://cdn.simpleicons.org/django/white",
    "react": "react/react-original.svg",
    "javascript": "javascript/javascript-original.svg",
    "typescript": "typescript/typescript-original.svg",
    "postgresql": "postgresql/postgresql-original.svg",
    "sqlite": "sqlite/sqlite-original.svg",
    "mysql": "mysql/mysql-original.svg",
    "git": "git/git-original.svg",
    "vscode": "vscode/vscode-original.svg",
    "pycharm": "pycharm/pycharm-original.svg",
    "docker": "docker/docker-original.svg",
    "nginx": "https://cdn.simpleicons.org/nginx/white",
    "redis": "redis/redis-original.svg",
    "aws": "https://cdn.simpleicons.org/amazon-aws/FF9900",
    "html": "html5/html5-original.svg",
    "css": "css3/css3-original.svg",
    "sql": "postgresql/postgresql-original.svg",
    "bash": "bash/bash-original.svg",
    "linux": "linux/linux-original.svg",
    "celery": "celery/celery-original.svg",
    "bootstrap": "bootstrap/bootstrap-original.svg"
}

def clean_content(text):
    """
    Cleans content by stripping leading/trailing whitespace and removing
    separator lines like '---' at the beginning or end of text blocks.
    """
    if not text:
        return ""
    text = text.strip()
    lines = text.splitlines()
    while lines and (lines[0].strip() == "---" or lines[0].strip() == ""):
        lines.pop(0)
    while lines and (lines[-1].strip() == "---" or lines[-1].strip() == ""):
        lines.pop()
    return "\n".join(lines).strip()

def markdown_to_html(text):
    """
    Translates simple markdown constructs (bold, italics, links, lists, paragraphs)
    to pure HTML elements and ensures no blank lines are present in the final HTML.
    This prevents GitHub from escaping outer table tags.
    """
    if not text:
        return ""
        
    text = clean_content(text)
    
    # Convert consecutive spaces (2 or more) to &nbsp; to preserve wide spacing formatting
    text = re.sub(r' {2,}', lambda m: '&nbsp;' * len(m.group(0)), text)
    
    # Convert bold: **text** to <strong>text</strong>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Convert italics: *text* to <em>text</em>
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    # Convert links: [text](url) to <a href="\2">\1</a>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Split by paragraph blocks (double newlines)
    blocks = re.split(r'\n\s*\n', text)
    html_blocks = []
    
    for block in blocks:
        block_str = block.strip()
        if not block_str:
            continue
            
        # Check if list block
        if block_str.startswith("- ") or block_str.startswith("* "):
            list_items = []
            for line in block_str.splitlines():
                line_str = line.strip()
                m = re.match(r"^[-*]\s+(.+)$", line_str)
                if m:
                    list_items.append(f"<li>{m.group(1)}</li>")
            html_blocks.append(f'<ul style="padding-left: 16px; margin: 0;">{"".join(list_items)}</ul>')
        else:
            # Paragraph formatting: join single newlines within a block into single paragraph
            para_content = block_str.replace("\n", " ")
            html_blocks.append(f'<p style="margin: 0 0 10px 0;">{para_content}</p>')
            
    # Filter and join blocks cleanly without extra blank lines
    filtered_blocks = [block.strip() for block in html_blocks if block.strip()]
    return "".join(filtered_blocks)

def parse_markdown_sections(filepath):
    """
    Parses content/CONTENT.md into major sections split by '# SECTION_NAME'.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Content file not found at: {filepath}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    sections = {}
    current_section = None
    section_content = []
    
    for line in content.splitlines():
        match = re.match(r"^#\s+(.+)$", line)
        if match:
            if current_section:
                sections[current_section] = clean_content("\n".join(section_content))
            current_section = match.group(1).strip().upper()
            section_content = []
        else:
            if current_section is not None:
                section_content.append(line)
                
    if current_section:
        sections[current_section] = clean_content("\n".join(section_content))
        
    return sections

def parse_subsections(text):
    """
    Parses subsections within a text block separated by '## Heading'.
    """
    subsections = []
    current_sub = None
    sub_content = []
    
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current_sub:
                subsections.append((current_sub, clean_content("\n".join(sub_content))))
            current_sub = match.group(1).strip()
            sub_content = []
        else:
            if current_sub is not None:
                sub_content.append(line)
                
    if current_sub:
        subsections.append((current_sub, clean_content("\n".join(sub_content))))
        
    return subsections

def parse_projects(text):
    """
    Parses project entries under BEST WORK SO FAR.
    Projects are headed by '## Project Name' and contain fields headed by '### Field'.
    """
    projects = []
    current_project = None
    project_data = {}
    current_field = None
    field_content = []
    description_lines = []
    
    for line in text.splitlines():
        p_match = re.match(r"^##\s+(.+)$", line)
        if p_match:
            if current_project:
                if current_field:
                    project_data[current_field] = clean_content("\n".join(field_content))
                project_data["description"] = clean_content("\n".join(description_lines))
                projects.append((current_project, project_data))
            current_project = p_match.group(1).strip()
            project_data = {}
            current_field = None
            field_content = []
            description_lines = []
        elif line.startswith("### "):
            if current_field:
                project_data[current_field] = clean_content("\n".join(field_content))
            current_field = line[4:].strip().lower()
            field_content = []
        else:
            if current_project:
                if current_field:
                    field_content.append(line)
                else:
                    description_lines.append(line)
                    
    if current_project:
        if current_field:
            project_data[current_field] = clean_content("\n".join(field_content))
        project_data["description"] = clean_content("\n".join(description_lines))
        projects.append((current_project, project_data))
        
    return projects

def parse_tech_stack(text):
    """
    Parses TECH STACK into lists of items per category heading.
    Supports items listed directly under # TECH STACK (using empty category string).
    """
    categories = []
    current_category = ""
    items = []
    
    for line in text.splitlines():
        line_str = line.strip()
        if not line_str:
            continue
            
        match = re.match(r"^##\s+(.+)$", line_str)
        if match:
            if items:
                categories.append((current_category, items))
            current_category = match.group(1).strip()
            items = []
        else:
            item_match = re.match(r"^[-*]\s+(.+)$", line_str)
            if item_match:
                items.append(item_match.group(1).strip())
                
    if items:
        categories.append((current_category, items))
        
    return categories

def make_project_badges(tech_stack_text):
    """
    Generates Shields.io badges for technology tags of projects.
    """
    if not tech_stack_text:
        return ""
    items = re.findall(r"^[-*]\s+(.+)$", tech_stack_text, re.MULTILINE)
    badges = []
    for item in items:
        clean_name = item.strip()
        badge_name = clean_name.replace("-", "--").replace(" ", "%20")
        badge_url = f"https://img.shields.io/badge/{badge_name}-3e4a3c?style=flat-square"
        badges.append(f'<img src="{badge_url}" alt="{clean_name}">&nbsp;')
    return "".join(badges)

def build_tech_stack_html(categories):
    """
    Builds a responsive wrapping grid of Devicon SVG logos for the tech stack
    without using nested tables.
    """
    html_parts = []
    for category, items in categories:
        if category.strip() != "":
            html_parts.append(f"<strong style=\"display: block; margin-top: 10px; margin-bottom: 5px;\">{category}</strong>")
        icons_html = []
        for item in items:
            clean_name = item.lower().strip()
            
            # Special white logo badge for GitHub in the tech stack
            if clean_name == "github":
                icon_url = "https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white"
                icons_html.append(f'<img src="{icon_url}" alt="{item}" title="{item}" style="margin: 5px 12px 5px 0; vertical-align: middle;">')
                continue
                
            icon_path = DEVICON_MAP.get(clean_name)
            if icon_path:
                if icon_path.startswith("http"):
                    # Direct URL (Simple Icons)
                    icons_html.append(f'<img src="{icon_path}" width="38" height="38" alt="{item}" title="{item}" style="margin: 5px 12px 5px 0; vertical-align: middle;">')
                else:
                    # Devicon path
                    icon_url = f"https://cdn.jsdelivr.net/gh/devicons/devicon/icons/{icon_path}"
                    icons_html.append(f'<img src="{icon_url}" width="38" height="38" alt="{item}" title="{item}" style="margin: 5px 12px 5px 0; vertical-align: middle;">')
            else:
                badge_url = f"https://img.shields.io/badge/{item.replace(' ', '%20')}-3e4a3c?style=flat-square"
                icons_html.append(f'<img src="{badge_url}" alt="{item}" title="{item}" style="margin: 5px 12px 5px 0; vertical-align: middle;">')
        html_parts.append("".join(icons_html))
        html_parts.append("<br>")
    return "".join(html_parts)

def build_connect_links(connect_text):
    """
    Parses contact details and renders them with vertically aligned white icons.
    """
    subsections = parse_subsections(connect_text)
    links = {title.lower().strip(): val.strip() for title, val in subsections}
    
    html_parts = []
    
    # LinkedIn
    if "linkedin" in links:
        li = links["linkedin"]
        html_parts.append(f'''
<p style="margin: 0 0 10px 0;">
  <img src="https://img.icons8.com/ios-glyphs/30/ffffff/linkedin.png" width="16" height="16" style="vertical-align: middle; margin-right: 8px;">
  <a href="https://linkedin.com/in/{li}" style="vertical-align: middle;">{li}</a>
</p>
        '''.strip())
    # Email
    if "email" in links:
        em = links["email"]
        html_parts.append(f'''
<p style="margin: 0 0 10px 0;">
  <img src="https://img.icons8.com/ios-glyphs/30/ffffff/new-post.png" width="16" height="16" style="vertical-align: middle; margin-right: 8px;">
  <a href="mailto:{em}" style="vertical-align: middle;">{em}</a>
</p>
        '''.strip())
    # GitHub
    if "github" in links:
        gh = links["github"]
        html_parts.append(f'''
<p style="margin: 0 0 10px 0;">
  <img src="https://img.icons8.com/ios-glyphs/30/ffffff/github.png" width="16" height="16" style="vertical-align: middle; margin-right: 8px;">
  <a href="https://github.com/{gh}" style="vertical-align: middle;">{gh}</a>
</p>
        '''.strip())
    # Portfolio
    if "portfolio" in links:
        pf = links["portfolio"]
        if pf.lower().startswith("http"):
            pf_url = pf
            pf_display = pf.replace("https://", "").replace("http://", "").split("/")[0]
        else:
            pf_url = f"https://{pf}"
            pf_display = pf
        html_parts.append(f'''
<p style="margin: 0 0 10px 0;">
  <img src="https://img.icons8.com/ios-glyphs/30/ffffff/globe.png" width="16" height="16" style="vertical-align: middle; margin-right: 8px;">
  <a href="{pf_url}" style="vertical-align: middle;">{pf_display}</a>
</p>
        '''.strip())
            
    return "\n".join(html_parts)

def main():
    content_file = "content/CONTENT.md"
    readme_file = "README.md"
    
    print(f"Reading and validating {content_file}...")
    try:
        sections = parse_markdown_sections(content_file)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Validate required sections
    REQUIRED_SECTIONS = [
        "HERO", "DIVIDER", "ROOTED IN", "RIGHT NOW", 
        "BEST WORK SO FAR", "MAJOR MILESTONES", "TECH STACK", 
        "GITHUB ACTIVITY", "LOOKING AHEAD", "LET'S CONNECT"
    ]
    missing = [sec for sec in REQUIRED_SECTIONS if sec not in sections]
    if missing:
        print(f"ERROR: Missing required sections in {content_file}: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
        
    print("Parsing sections...")
    
    # 1. Divider
    divider_text = markdown_to_html(sections["DIVIDER"])
    # Strip any outer paragraph tags added by the converter
    divider_text = re.sub(r'^<p[^>]*>(.*)</p>$', r'\1', divider_text.strip())
    
    # 2. Rooted In
    rooted_in_text = markdown_to_html(sections["ROOTED IN"])
    
    # 3. Right Now
    right_now_text = sections["RIGHT NOW"]
    right_now_subs = parse_subsections(right_now_text)
    
    # 4. Best Work So Far
    best_work_text = sections["BEST WORK SO FAR"]
    projects = parse_projects(best_work_text)
    
    # 5. Major Milestones
    milestones_text = sections["MAJOR MILESTONES"]
    milestone_entries = parse_subsections(milestones_text)
    
    # 6. Tech Stack
    tech_text = sections["TECH STACK"]
    tech_categories = parse_tech_stack(tech_text)
    
    # 7. Looking Ahead
    looking_ahead_text = markdown_to_html(sections["LOOKING AHEAD"])
    
    # 8. Let's Connect
    connect_text = sections["LET'S CONNECT"]
    
    # Build HTML for Right Now (Simple blocks, no nested tables to avoid borders)
    right_now_html = []
    for title, content in right_now_subs:
        icon = "🌱"
        if title.lower() == "building":
            icon = "💻"
        elif title.lower() == "learning":
            icon = "📖"
        elif title.lower() == "exploring":
            icon = "🚀"
        elif title.lower() == "reading":
            icon = "📄"
            
        content_html = markdown_to_html(content)
        right_now_html.append(f'''
<p style="margin: 0 0 6px 0;">{icon} <strong>{title}</strong></p>
{content_html}
        '''.strip())
    right_now_rows = "\n".join(right_now_html)
    
    # Build HTML for Best Work So Far
    projects_html = []
    for name, data in projects:
        desc = data.get("description", "")
        tech = data.get("tech stack", "")
        repo = data.get("repository", "")
        status = data.get("status", "")
        
        badges = make_project_badges(tech)
        repo_link = ""
        if repo:
            clean_repo = repo.strip()
            if not clean_repo.startswith("http"):
                repo_url = f"https://github.com/{clean_repo}"
            else:
                repo_url = clean_repo
            repo_link = f"<br>🔗&nbsp;<a href=\"{repo_url}\">{clean_repo}</a>"
        status_line = f"<br><em>Status: {status}</em>" if status else ""
        
        projects_html.append(f'''
<p><strong>{name}</strong>{status_line}<br>
{desc}<br><br>
{badges}
{repo_link}</p>
<br>
        '''.strip())
    projects_content = "".join(projects_html)
    
    # Build HTML for Major Milestones (pure float-based divs, zero tables to avoid GFM borders)
    milestones_html = []
    for year, desc in milestone_entries:
        desc_html = markdown_to_html(desc)
        icon = "🚀" if year.lower() == "looking forward" else year
        milestones_html.append(f'''
<div style="margin: 0 0 12px 0; line-height: 1.5; clear: both;">
  <div style="float: left; width: 50px; font-weight: bold; color: #8b949e;">{icon}</div>
  <div style="float: left; width: 30px; text-align: center; color: #3e4a3c;">✦</div>
  <div style="overflow: hidden;">
    {desc_html}
  </div>
</div>
        '''.strip())
    milestone_rows = "\n".join(milestones_html)
    
    # Build Tech Stack
    tech_stack_content = build_tech_stack_html(tech_categories)
    
    # Build Connect
    connect_content_html = build_connect_links(connect_text)
    
    # Generate Output README with auto-generated warning (No blank lines between table blocks to tighten rendering)
    readme_template = f'''<!--
This file is auto-generated. Do not edit directly.
Source: content/CONTENT.md
Generator: scripts/generate_readme.py
-->
<div align="center">
  <img src="assets/hero-banner.png" width="100%" alt="Hero Banner">
</div>
<p align="center" style="margin-top: 16px; margin-bottom: 16px;">
  {divider_text}
</p>
<!-- Row 1: Rooted In, Right Now, Best Work So Far (Unified Equal Heights Layout) -->
<table width="100%" style="border-collapse: collapse; border: 1px solid #3e382b !important; border-radius: 6px; background-color: #000000; margin-bottom: 16px;">
  <tr valign="top" style="border: 0 !important;">
    <!-- Rooted In Column -->
    <td width="33.3%" style="padding: 16px; border: 0 !important; border-right: 1px solid #3e382b !important;" valign="top">
      <h3 style="margin: 0 0 16px 0;">🌱 Rooted In</h3>{rooted_in_text}
    </td>
    <!-- Right Now Column -->
    <td width="33.3%" style="padding: 16px; border: 0 !important; border-right: 1px solid #3e382b !important;" valign="top">
      <h3 style="margin: 0 0 16px 0;">🚀 Right Now</h3>
      {right_now_rows}
    </td>
    <!-- Best Work So Far Column -->
    <td width="33.4%" style="padding: 16px; border: 0 !important;" valign="top">
      <h3 style="margin: 0 0 16px 0;">🌸 Best Work So Far</h3>{projects_content}
    </td>
  </tr>
</table>
<!-- Row 2: Major Milestones, Tech Stack (Unified Equal Heights Layout) -->
<table width="100%" style="border-collapse: collapse; border: 1px solid #3e382b !important; border-radius: 6px; background-color: #000000; margin-bottom: 16px;">
  <tr valign="top" style="border: 0 !important;">
    <!-- Major Milestones Column -->
    <td width="60%" style="padding: 16px; border: 0 !important; border-right: 1px solid #3e382b !important;" valign="top">
      <h3 style="margin: 0 0 16px 0;">🌙 Major Milestones</h3>
      {milestone_rows}
    </td>
    <!-- Tech Stack Column -->
    <td width="40%" style="padding: 16px; border: 0 !important;" valign="top">
      <h3 style="margin: 0 0 16px 0;">⚙️ Tech Stack</h3>{tech_stack_content}
    </td>
  </tr>
</table>
<!-- GitHub Activity (Full Width Card) -->
<table width="100%" style="border-collapse: collapse; border: 1px solid #3e382b !important; border-radius: 6px; background-color: #000000; margin-bottom: 16px;">
  <tr style="border: 0 !important;">
    <td style="padding: 16px; border: 0 !important;">
      <h3 style="margin: 0 0 16px 0;">📊 GitHub Activity</h3>
      <div align="center">
        <img src="https://github-readme-stats.vercel.app/api?username=Farheen-H-S&show_icons=true&theme=react&hide_border=true" alt="GitHub Stats"><br><br>
        <img src="https://github-readme-activity-graph.vercel.app/graph?username=Farheen-H-S&theme=react&hide_border=true&area=true" width="100%" alt="Activity Graph">
      </div>
    </td>
  </tr>
</table>
<!-- Final Row: Looking Ahead, Let's Connect (Unified Equal Heights Layout) -->
<table width="100%" style="border-collapse: collapse; border: 1px solid #3e382b !important; border-radius: 6px; background-color: #000000;">
  <tr valign="top" style="border: 0 !important;">
    <!-- Looking Ahead Column -->
    <td width="50%" style="padding: 16px; border: 0 !important; border-right: 1px solid #3e382b !important;" valign="top">
      <h3 style="margin: 0 0 16px 0;">★ Looking Ahead</h3>{looking_ahead_text}
    </td>
    <!-- Let's Connect Column -->
    <td width="50%" style="padding: 16px; border: 0 !important;" valign="top">
      <img src="assets/lets-connect-flower.png" align="right" width="150" style="margin-left: 12px; margin-top: 10px;" alt="Connect Flower">
      <h3 style="margin: 0 0 16px 0;">🌱 Let's Connect</h3>
      {connect_content_html}
    </td>
  </tr>
</table>
'''
    
    print(f"Writing compiled output to {readme_file}...")
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_template.strip() + "\n")
        
    print("Generation complete! README.md successfully rebuilt.")

if __name__ == "__main__":
    main()
