"""Robust title extraction for the D4GC corpus (HTML, PDF, and Markdown)."""
from pathlib import Path
import re

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

BOILERPLATE_PREFIXES = (
    "all rights reserved", "contents lists available", "journal homepage",
    "www.", "http:", "https:", "doi:", "available online", "conflict of interest",
    "the author has declared", "viewpoint", "review", "articles", "original article",
    "short communication", "special report", "case report", "editorial",
    "letters to the editor", "transactions of the", "international health",
    "the new england journal", "the new engl", "n engl j med", "lancet",
    "bmj", "plos", "annals of", "bulletin of the", "american journal of",
    "english charity reg", "permalink", "on this page", "aller au contenu",
    "passer au contenu", "skip to main", "table of contents", "sommaire",
    "la nouvelle application", "the new app", "item type", "authors",
    "received", "accepted", "published", "copyright", "volume", "vol.", "issue",
    "page", "pages", "e-mail:", "email:", "correspondence to", "abstract",
    "résumé", "resumen", "acknowledgments", "funding", "keywords",
    "mov % calculated", "chi squared test", "accepted manuscript",
    "meeting report", "open access"
)

def is_boilerplate(line):
    clean = line.strip().lower()
    if not clean or len(clean) < 3:
        return True
    if re.match(r"^e?\d+[\s\-\u2013\u2014\d]*$", clean):
        return True
    for bp in BOILERPLATE_PREFIXES:
        if clean.startswith(bp):
            return True
    if "www." in clean or "http:" in clean or "https:" in clean or "@" in clean:
        return True
    if "creative commons attribution" in clean or "license (http" in clean or "licence (http" in clean:
        return True
    return False

def is_author_boundary(line):
    clean = line.strip()
    clean_lower = clean.lower()
    
    if clean_lower in ("authors", "item type", "abstract", "summary", "keywords", "background", "methods"):
        return True
    if clean_lower.startswith(("item type", "authors:", "correspondence", "author details", "affiliation")):
        return True
    if re.search(r"\b(m\.d\.|ph\.d\.|m\.p\.h\.|m\.sc\.|b\.sc\.|m\.b\.b\.s\.)\b", clean_lower):
        return True
    if re.search(r"\b(department of|centre for|university|hospital|institut|médecins sans frontières|msf|epicentre|ministry of health)\b", clean_lower):
        return True
    if re.search(r"[a-zA-Z]+[0-9a-f],\*|[a-zA-Z]+[0-9]+,[0-9]+", clean):
        return True
    if re.search(r"\b(corresponding author|contributed equally)\b", clean_lower):
        return True
    if ";" in clean and len(clean.split(";")) >= 2:
        return True
    if clean.count(",") >= 3 and not re.search(r"\b(and|or|for|with|in|of|the)\b", clean_lower):
        return True
    if re.search(r"^[A-Z]\.?\s+[A-Z][a-z]+.*,", clean):
        return True
    return False

def clean_title_string(t):
    if not t:
        return ""
    t = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", t)
    t = re.sub(r"[*_#`]", "", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*\|\s*(MSF.*|Guides médicaux.*|Médecins Sans Frontières.*|Medical Guidelines.*)$", "", t, flags=re.I)
    return t.strip()

def extract_html_title(html_path):
    if not html_path or not html_path.exists():
        return None
    try:
        content = html_path.read_text(encoding="utf-8", errors="replace")
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.I | re.S)
        if h1_match:
            candidate = clean_title_string(re.sub(r"<[^>]+>", "", h1_match.group(1)))
            if candidate and not is_boilerplate(candidate) and len(candidate) > 4:
                return candidate
        title_match = re.search(r"<title>(.*?)</title>", content, re.I | re.S)
        if title_match:
            candidate = clean_title_string(re.sub(r"<[^>]+>", "", title_match.group(1)))
            if candidate and not is_boilerplate(candidate) and len(candidate) > 4:
                return candidate
    except Exception:
        pass
    return None

def extract_pdf_meta_title(pdf_path, text):
    if not PyPDF2 or not pdf_path or not pdf_path.exists():
        return None
    try:
        reader = PyPDF2.PdfReader(str(pdf_path))
        meta = reader.metadata or {}
        raw = meta.get('/Title')
        if raw and isinstance(raw, str):
            clean = clean_title_string(raw)
            clean_lower = clean.lower()
            if (len(clean) > 12 and 
                not clean_lower.startswith(('untitled', 'doi:', 'microsoft word', 'poster_abstract', 'slide')) and
                not is_boilerplate(clean)):
                # Verify that key terms appear in the markdown text
                words = [w for w in re.findall(r"\w+", clean_lower) if len(w) > 3]
                text_lower = text[:4000].lower()
                matches = sum(1 for w in words if w in text_lower)
                if len(words) == 0 or matches / len(words) >= 0.5:
                    return clean
    except Exception:
        pass
    return None

def extract_markdown_title(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ""

    for l in lines[:15]:
        if l.startswith("# "):
            candidate = clean_title_string(l.lstrip("# "))
            if candidate and not is_boilerplate(candidate) and not is_author_boundary(candidate):
                return candidate[:220]

    title_parts = []
    for l in lines[:35]:
        clean_l = clean_title_string(l)
        if not clean_l:
            continue
        if not title_parts:
            if is_boilerplate(clean_l) or is_author_boundary(clean_l):
                continue
            title_parts.append(clean_l)
            if clean_l.endswith((".", "?", "!")) and len(clean_l) > 45:
                break
        else:
            if is_author_boundary(clean_l) or is_boilerplate(clean_l):
                break
            title_parts.append(clean_l)
            if len(" ".join(title_parts)) > 190 or clean_l.endswith((".", "?", "!")):
                break

    if title_parts:
        candidate = clean_title_string(" ".join(title_parts))
        if len(candidate) > 5:
            return candidate[:220]

    return ""

def extract_clean_title(doc_id, text, orig_path=None):
    orig_path = Path(orig_path) if orig_path else None
    
    # 1. HTML title tag or <h1>
    if orig_path and orig_path.suffix.lower() == ".html" and orig_path.exists():
        t = extract_html_title(orig_path)
        if t:
            return t

    # 2. PDF metadata title
    if orig_path and orig_path.suffix.lower() == ".pdf" and orig_path.exists():
        t = extract_pdf_meta_title(orig_path, text)
        if t:
            return t

    # 3. Markdown text analysis
    t = extract_markdown_title(text)
    if t:
        return t

    return doc_id
