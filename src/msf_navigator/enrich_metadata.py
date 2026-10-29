"""Conservative, reproducible metadata enrichment for the supplied D4GC corpus.

Locations are text mentions, never inferred primary locations. Edit the lexicons
below as the team reviews examples; this module needs only Python's stdlib.
"""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import re

from .title_extractor import extract_clean_title

from .paths import ROOT, CORPUS, ENRICHED_METADATA
SOURCE = ROOT / "data" / "documentation.csv"
BASE = CORPUS
OUTPUT = ENRICHED_METADATA

# Canonical labels with selected English, French, Spanish and common variants.
# Intentionally incomplete: blank means no match in this lexicon, not no location.
COUNTRIES = {
    "Afghanistan": ["Afghanistan"], "Bangladesh": ["Bangladesh"],
    "Belgium": ["Belgium", "Belgique", "Bélgica"],
    "Brazil": ["Brazil", "Brasil", "Brésil"],
    "Burkina Faso": ["Burkina Faso"], "Burundi": ["Burundi"],
    "Cameroon": ["Cameroon", "Cameroun", "Camerún"],
    "Central African Republic": ["Central African Republic", "République centrafricaine"],
    "Chad": ["Chad", "Tchad"], "China": ["China", "Chine", "China"],
    "Colombia": ["Colombia", "Colombie"],
    "Democratic Republic of the Congo": ["Democratic Republic of the Congo", "DR Congo", "DRC", "RDC", "République démocratique du Congo"],
    "Ethiopia": ["Ethiopia", "Éthiopie", "Etiopía"],
    "France": ["France", "Francia"],
    "Guinea": ["Guinea", "Guinée"], "Haiti": ["Haiti", "Haïti", "Haití"],
    "India": ["India", "Inde"], "Indonesia": ["Indonesia", "Indonésie"],
    "Iraq": ["Iraq", "Irak"], "Jordan": ["Jordan", "Jordanie", "Jordania"],
    "Kenya": ["Kenya"], "Lebanon": ["Lebanon", "Liban", "Líbano"],
    "Liberia": ["Liberia", "Libéria"], "Libya": ["Libya", "Libye", "Libia"],
    "Mali": ["Mali"], "Mexico": ["Mexico", "Mexique", "México"],
    "Mozambique": ["Mozambique"], "Myanmar": ["Myanmar", "Burma", "Birmanie"],
    "Nepal": ["Nepal", "Népal"], "Niger": ["Niger"],
    "Nigeria": ["Nigeria", "Nigéria"], "Pakistan": ["Pakistan"],
    "Palestine": ["Palestine", "Palestina"],
    "Philippines": ["Philippines", "Filipinas"],
    "Sierra Leone": ["Sierra Leone"], "Somalia": ["Somalia", "Somalie"],
    "South Africa": ["South Africa", "Afrique du Sud", "Sudáfrica"],
    "South Sudan": ["South Sudan", "Soudan du Sud", "Sudán del Sur"],
    "Sudan": ["Sudan", "Soudan", "Sudán"],
    "Syria": ["Syria", "Syrie", "Siria"],
    "Tanzania": ["Tanzania", "Tanzanie"], "Thailand": ["Thailand", "Thaïlande", "Tailandia"],
    "Turkey": ["Turkey", "Türkiye", "Turquie", "Turquía"],
    "Uganda": ["Uganda", "Ouganda"], "Ukraine": ["Ukraine", "Ucrania"],
    "United Kingdom": ["United Kingdom", "Royaume-Uni", "UK"],
    "United States": ["United States", "États-Unis", "USA"],
    "Yemen": ["Yemen", "Yémen"], "Zimbabwe": ["Zimbabwe"],
}
CITIES = {
    "Aleppo": ["Aleppo", "Alep"], "Amman": ["Amman"],
    "Bangui": ["Bangui"], "Beirut": ["Beirut", "Beyrouth"],
    "Brussels": ["Brussels", "Bruxelles", "Brussel"],
    "Cox's Bazar": ["Cox's Bazar", "Cox’s Bazar"],
    "Damascus": ["Damascus", "Damas", "Damasco"],
    "Dhaka": ["Dhaka"], "Goma": ["Goma"], "Gaza City": ["Gaza City"],
    "Hodeidah": ["Hodeidah", "Hudaydah"], "Juba": ["Juba"],
    "Kabul": ["Kabul"], "Kampala": ["Kampala"],
    "Khartoum": ["Khartoum"], "Kinshasa": ["Kinshasa"],
    "Lagos": ["Lagos"], "Mogadishu": ["Mogadishu", "Mogadiscio"],
    "Mosul": ["Mosul", "Mossoul"], "Nairobi": ["Nairobi"],
    "Port-au-Prince": ["Port-au-Prince"], "Raqqa": ["Raqqa", "Raqa"],
    "Sana'a": ["Sana'a", "Sanaa"], "Tripoli": ["Tripoli"],
}
TOPICS = {
    "cholera": ["cholera", "choléra", "cólera"],
    "tuberculosis": ["tuberculosis", "tuberculose", "tuberculosis"],
    "malnutrition": ["malnutrition", "malnutrición"],
    "vaccination": ["vaccination", "vaccine", "vaccin", "vacunación"],
    "maternal_health": ["maternal", "maternité", "maternidad", "pregnancy"],
    "mental_health": ["mental health", "santé mentale", "salud mental"],
    "surgery": ["surgery", "chirurgie", "cirugía"],
    "displacement": ["refugee", "réfugié", "refugiado", "displaced", "déplacé"],
    "epidemic": ["epidemic", "épidémie", "epidemia", "outbreak"],
    "water_sanitation": ["sanitation", "assainissement", "saneamiento", "water supply"],
}


def matcher(lexicon):
    aliases = {alias.casefold(): label for label, values in lexicon.items() for alias in values}
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True)) + r")(?!\w)", re.I)
    return pattern, aliases


def mentions(text, compiled):
    pattern, aliases = compiled
    matches = list(pattern.finditer(text))
    labels = sorted({aliases[m.group().casefold()] for m in matches})
    evidence = ""
    if matches:
        m = matches[0]
        evidence = re.sub(r"\s+", " ", text[max(0, m.start()-55):m.end()+55]).strip()
    return "|".join(labels), evidence


def run(output=OUTPUT):
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    originals = {p.stem: p for p in (BASE / "Original").iterdir() if p.is_file()}
    country_matcher, city_matcher, topic_matcher = map(matcher, (COUNTRIES, CITIES, TOPICS))
    hashes = Counter()
    for row in rows:
        doc_id = row["id"]
        parsed = BASE / "Parsed" / f"{doc_id}.md"
        original = originals.get(doc_id)
        text = parsed.read_text(encoding="utf-8", errors="replace") if parsed.exists() else ""
        countries, country_evidence = mentions(text, country_matcher)
        cities, city_evidence = mentions(text, city_matcher)
        topics, _ = mentions(text, topic_matcher)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""
        if digest:
            hashes[digest] += 1
        title = extract_clean_title(doc_id, text, original) if text else doc_id
        row.update({
            "title": title,
            "parsed_available": str(parsed.exists()).lower(),
            "original_available": str(original is not None).lower(),
            "parsed_path": parsed.relative_to(ROOT).as_posix() if parsed.exists() else "",
            "original_path": original.relative_to(ROOT).as_posix() if original else "",
            "source_format": original.suffix.lower().lstrip(".") if original else "",
            "word_count": str(len(re.findall(r"\w+", text, re.UNICODE))) if text else "",
            "text_sha256": digest,
            "country_mentions": countries,
            "city_mentions": cities,
            "topic_tags": topics,
            "country_evidence": country_evidence,
            "city_evidence": city_evidence,
            "geography_review_required": str(bool(countries or cities)).lower(),
            "extraction_method": "curated_lexicon_v1" if text else "no_parsed_text",
        })
    for row in rows:
        row["duplicate_text_group_size"] = str(hashes[row["text_sha256"]]) if row["text_sha256"] else ""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    print(f"Wrote {len(run())} rows to {OUTPUT}")
